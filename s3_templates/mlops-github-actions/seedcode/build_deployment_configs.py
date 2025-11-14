import argparse
import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def get_approved_package(model_package_group_name, sm_client):
    """Gets the latest approved model package for a model package group.

    Args:
        model_package_group_name: The model package group name.

    Returns:
        The SageMaker Model Package ARN.
    """
    try:
        # Get the latest approved model package
        response = sm_client.list_model_packages(
            ModelPackageGroupName=model_package_group_name,
            ModelApprovalStatus="Approved",
            SortBy="CreationTime",
            MaxResults=100,
        )
        approved_packages = response["ModelPackageSummaryList"]

        # Fetch more packages if none returned with continuation token
        while len(approved_packages) == 0 and "NextToken" in response:
            logger.debug(
                "Getting more packages for token: {}".format(
                    response["NextToken"]
                )
            )
            response = sm_client.list_model_packages(
                ModelPackageGroupName=model_package_group_name,
                ModelApprovalStatus="Approved",
                SortBy="CreationTime",
                MaxResults=100,
                NextToken=response["NextToken"],
            )
            approved_packages.extend(response["ModelPackageSummaryList"])

        # Return error if no packages found
        if len(approved_packages) == 0:
            error_message = f"No approved ModelPackage found."
            logger.error(error_message)
            raise Exception(error_message)

        # Return the pmodel package arn
        model_package_arn = approved_packages[0]["ModelPackageArn"]
        logger.debug(
            f"Identified the latest approved model package: {model_package_arn}"
        )
        return model_package_arn
    except ClientError as e:
        error_message = e.response["Error"]["Message"]
        logger.error(error_message)
        raise Exception(error_message)


def extend_config(
    args,
    model_package_arn,
    stage_config,
    sm_client,
    project_id,
    project_arn,
    model_execution_role,
):
    """
    Extend the stage configuration with additional parameters and tags based.
    """
    # Verify that config has parameters and tags sections
    if (
        not "Parameters" in stage_config
        or not "StageName" in stage_config["Parameters"]
    ):
        raise Exception("Configuration file must include SageName parameter")
    if not "Tags" in stage_config:
        stage_config["Tags"] = {}
    # Create new params and tags
    new_params = {
        "SageMakerProjectName": args.sagemaker_project_name,
        "ModelPackageName": model_package_arn,
        "ModelExecutionRoleArn": model_execution_role,
    }
    new_tags = {
        "sagemaker:deployment-stage": stage_config["Parameters"]["StageName"],
        "sagemaker:project-id": project_id,
        "sagemaker:project-name": args.sagemaker_project_name,
    }
    # Add tags from Project
    get_pipeline_custom_tags(args, sm_client, new_tags, project_arn)

    return {
        "Parameters": {**stage_config["Parameters"], **new_params},
        "Tags": {**stage_config.get("Tags", {}), **new_tags},
    }


def get_pipeline_custom_tags(args, sm_client, new_tags, project_arn):
    try:
        response = sm_client.list_tags(ResourceArn=project_arn)
        project_tags = response["Tags"]
        for project_tag in project_tags:
            new_tags[project_tag["Key"]] = project_tag["Value"]
    except Exception:
        logger.error("Error getting project tags")
    return new_tags


def get_cfn_style_config(stage_config):
    parameters = []
    for key, value in stage_config["Parameters"].items():
        parameter = {"ParameterKey": key, "ParameterValue": value}
        parameters.append(parameter)
    tags = []
    for key, value in stage_config["Tags"].items():
        tag = {"Key": key, "Value": value}
        tags.append(tag)
    return parameters, tags


def create_cfn_params_tags_file(config, export_params_file, export_tags_file):
    # Write Params and tags in separate file for Cfn cli command
    parameters, tags = get_cfn_style_config(config)
    with open(export_params_file, "w") as f:
        json.dump(parameters, f, indent=4)
    with open(export_tags_file, "w") as f:
        json.dump(tags, f, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--log-level",
        type=str,
        default=os.environ.get("LOGLEVEL", "INFO").upper(),
    )
    parser.add_argument("--sagemaker-project-name", type=str, required=True)
    parser.add_argument("--region", type=str, required=True)
    parser.add_argument(
        "--model-package-group-name",
        type=str,
        required=False,
        help="default to ProjectName-ProjectId",
    )
    parser.add_argument(
        "--import-staging-config", type=str, default="staging-config.json"
    )
    parser.add_argument(
        "--import-prod-config", type=str, default="prod-config.json"
    )
    parser.add_argument(
        "--export-staging-config",
        type=str,
        default="staging-config-export.json",
    )
    parser.add_argument(
        "--export-staging-params",
        type=str,
        default="staging-params-export.json",
    )
    parser.add_argument(
        "--export-staging-tags", type=str, default="staging-tags-export.json"
    )
    parser.add_argument(
        "--export-prod-config", type=str, default="prod-config-export.json"
    )
    parser.add_argument(
        "--export-prod-params", type=str, default="prod-params-export.json"
    )
    parser.add_argument(
        "--export-prod-tags", type=str, default="prod-tags-export.json"
    )
    parser.add_argument("--export-cfn-params-tags", type=bool, default=False)
    args, _ = parser.parse_known_args()

    # Configure logging to output the line number and message
    log_format = "%(levelname)s: [%(filename)s:%(lineno)s] %(message)s"
    logging.basicConfig(format=log_format, level=args.log_level)

    # Create SageMaker client
    sm_client = boto3.client("sagemaker", region_name=args.region)

    # Get SageMaker project info
    project_info = sm_client.describe_project(
        ProjectName=args.sagemaker_project_name
    )
    project_id = project_info["ProjectId"]
    project_arn = project_info["ProjectArn"]

    # Set Defaults
    if args.model_package_group_name:
        model_package_group_name = args.model_package_group_name
    else:
        model_package_group_name = (
            f"{args.sagemaker_project_name}-{project_id}"
        )

    # Get the latest approved package
    model_package_arn = get_approved_package(
        model_package_group_name, sm_client
    )

    # Get Model Execution Role
    sm_domain = sm_client.describe_domain(
        DomainId=project_info["CreatedBy"]["DomainId"]
    )
    execution_role_arn = sm_domain["DefaultUserSettings"]["ExecutionRole"]

    # Write the staging config
    with open(args.import_staging_config, "r") as f:
        staging_config = extend_config(
            args=args,
            model_package_arn=model_package_arn,
            stage_config=json.load(f),
            sm_client=sm_client,
            project_id=project_id,
            project_arn=project_arn,
            model_execution_role=execution_role_arn,
        )
    logger.debug(
        "Staging config: {}".format(json.dumps(staging_config, indent=4))
    )
    with open(args.export_staging_config, "w") as f:
        json.dump(staging_config, f, indent=4)
    if args.export_cfn_params_tags:
        create_cfn_params_tags_file(
            staging_config,
            args.export_staging_params,
            args.export_staging_tags,
        )

    # Write the prod config for code pipeline
    with open(args.import_prod_config, "r") as f:
        prod_config = extend_config(
            args=args,
            model_package_arn=model_package_arn,
            stage_config=json.load(f),
            sm_client=sm_client,
            project_id=project_id,
            project_arn=project_arn,
            model_execution_role=execution_role_arn,
        )
    logger.debug("Prod config: {}".format(json.dumps(prod_config, indent=4)))
    with open(args.export_prod_config, "w") as f:
        json.dump(prod_config, f, indent=4)
    if args.export_cfn_params_tags:
        create_cfn_params_tags_file(
            prod_config, args.export_prod_params, args.export_prod_tags
        )
