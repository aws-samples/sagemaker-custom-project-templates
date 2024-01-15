import argparse
import json
import logging
import os
import sys

import boto3
from botocore.exceptions import ClientError

from utils import (
    download_file_from_s3,
    check_if_model_package_exists,
    get_cfn_style_config,
    upload_file_to_s3,
    waits_model_package_complete,
)

LOG_FORMAT = "%(levelname)s: [%(filename)s:%(lineno)s] %(message)s"

logger = logging.getLogger(__name__)

dev_acc_boto3_session = boto3.Session(profile_name="dev")
target_acc_boto3_session = boto3.Session(profile_name="target")
dev_sm_client = dev_acc_boto3_session.client("sagemaker")
target_sm_client = target_acc_boto3_session.client("sagemaker")
dev_s3_client = dev_acc_boto3_session.client("s3")
target_s3_client = target_acc_boto3_session.client("s3")
target_ecr_client = target_acc_boto3_session.client("ecr")
ssm = target_acc_boto3_session.client("ssm")


def get_approved_package(model_package_group_name):
    """Gets the latest approved model package for a model package group.
    Args:model_package_group_name: The model package group name.
    Returns:The SageMaker Model Package ARN.
    """
    try:
        approved_packages = []
        # Find the latest approved model package.
        # If there are several approved model packages, take the most recent one (by CreationTime)
        for model_package in dev_sm_client.get_paginator(
            "list_model_packages"
        ).paginate(
            ModelPackageGroupName=model_package_group_name,
            ModelApprovalStatus="Approved",
            SortBy="CreationTime",
            SortOrder="Descending",
        ):
            approved_packages.extend(model_package["ModelPackageSummaryList"])

        # Raise error if no packages found
        if not approved_packages:
            logger.error(
                "No approved ModelPackage found for ModelPackageGroup: %s",
                model_package_group_name,
            )
            raise Exception(
                f"No approved ModelPackage found for {model_package_group_name}"
            )

        # Return the pmodel package arn
        package_arn = approved_packages[0]["ModelPackageArn"]
        logger.info("Identified the latest approved model package: %s", package_arn)
        package_version = approved_packages[0]["ModelPackageVersion"]
        return package_arn, package_version
    except ClientError as error:
        error_message = error.response["Error"]["Message"]
        logger.error(error_message)
        raise Exception(error_message) from error


def convert_package_definition(
    describe_response: dict, target_package_name: str, args
) -> dict:
    """Given a response from boto3.client("sagemaker").describe_model_package(),
    move artifacts into target account and translate the response so that it
    can be used with boto3.client("sagemaker").create_model_package() call.
    This function changes the container specification by moving the model binaries into
    target-bucket.

    Args: describe_response (dict), target_bucket_name (str)
    Returns: converted_dict (dict)
    """
    new_response = describe_response.copy()
    containers = describe_response["InferenceSpecification"]["Containers"]
    for i, container in enumerate(containers):
        s3_uri = container["ModelDataUrl"]
        local_path = f"model_{i}.tar.gz"
        upload_path = (
            f"s3://{target_bucket}/{args.sagemaker_project_name}-{args.sagemaker_project_id}/model-artifacts/"
            f"{target_package_name}/model_{i}.tar.gz"
        )

        download_file_from_s3(s3_uri, local_path, dev_s3_client)
        logger.info("Downloaded locally: %s to %s", s3_uri, local_path)
        upload_file_to_s3(local_path, upload_path, target_s3_client)
        logger.info("Uploaded: %s to %s", local_path, upload_path)
        new_response["InferenceSpecification"]["Containers"][i][
            "ModelDataUrl"
        ] = upload_path
        new_response["InferenceSpecification"]["Containers"][i]["Image"] = (
            container["Image"]
            .replace(args.training_id, args.target_id)
            .replace("dev", args.stage)
        )

        del new_response["InferenceSpecification"]["Containers"][i]["Environment"]

    keys_for_registering_model = ["InferenceSpecification"]

    return {key: new_response[key] for key in keys_for_registering_model}


def extend_config(script_args, model_arn, static_config):
    """Extend the stage configuration with additional parameters. SageMaker Project details
    and Model details. This function should be extended as required to pass on other
    dynamic configurations.
    """
    new_params = {
        "SageMakerProjectName": script_args.sagemaker_project_name,
        "SageMakerProjectId": script_args.sagemaker_project_id,
        "ModelPackageName": model_arn,
        "ProjectBucket": target_bucket,
        "Environment": script_args.environment,
        "SubnetIds": subnets,
        "SGIds": security_group_ids,
    }
    if script_args.code == "tf":
        parameters_dict = {**static_config, **new_params}
        return parameters_dict
    # else code=cfn
    parameters_dict = {**static_config["Parameters"], **new_params}
    return get_cfn_style_config(parameters_dict)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--log-level", type=str, default=os.environ.get("LOGLEVEL", "INFO").upper()
    )
    parser.add_argument("--sagemaker-project-name", type=str, required=True)
    parser.add_argument("--sagemaker-project-id", type=str, required=True)
    parser.add_argument("--model-package-group-name", type=str, required=True)
    parser.add_argument("--stage", type=str, required=True)
    parser.add_argument("--training-id", type=str, required=True)
    parser.add_argument("--target-id", type=str, required=True)
    parser.add_argument("--environment", type=str, required=True)
    parser.add_argument("--import-config", type=str, required=True)
    parser.add_argument("--export-config", type=str, required=True)
    parser.add_argument("--code", type=str, required=True)  # tf or cfn

    args, _ = parser.parse_known_args()

    # Configure logging to output the line number and message
    logging.basicConfig(format=LOG_FORMAT, level=args.log_level)

    # get target bucket, subnets and sg group from ssm

    target_bucket = ssm.get_parameter(
        Name=f"/{args.environment}/sagemaker_ml_artifacts_s3_bucket"
    )["Parameter"]["Value"]

    security_group_ids = ssm.get_parameter(Name=f"sagemaker-domain-sg")["Parameter"][
        "Value"
    ]
    subnets = ssm.get_parameter(Name=f"private-subnets-ids")["Parameter"]["Value"]

    # Get the latest approved package
    model_package_arn, version = get_approved_package(args.model_package_group_name)

    if target_model_package_name := check_if_model_package_exists(
        f"{args.sagemaker_project_name}-{args.stage}-v{version}", target_sm_client
    ):
        target_model_package_arn = target_sm_client.describe_model_package(
            ModelPackageName=target_model_package_name
        )["ModelPackageArn"]

    else:
        new_model_package_name = (
            f"{args.sagemaker_project_name}-{args.stage}-v{version}"
        )

        response = dev_sm_client.describe_model_package(
            ModelPackageName=model_package_arn
        )

        package_definition = convert_package_definition(
            response, new_model_package_name, args
        )
        target_model_package_arn = target_sm_client.create_model_package(
            ModelPackageName=new_model_package_name,
            ModelApprovalStatus="Approved",
            Tags=[
                {"Key": "sagemaker:project-name", "Value": args.sagemaker_project_name},
                {"Key": "sagemaker:project-id", "Value": args.sagemaker_project_id},
            ],
            **package_definition,
        )["ModelPackageArn"]
        logger.info(
            "Model created: %s",
            target_model_package_arn,
        )

        waits_model_package_complete(new_model_package_name, target_sm_client)

    # Extend the config file
    with open(args.import_config, "r", encoding="utf-8") as f:
        config = json.load(f)

    extended_config = extend_config(
        args,
        target_model_package_arn,
        config,
    )
    with open(args.export_config, "w", encoding="utf-8") as f:
        json.dump(extended_config, f, indent=4)
