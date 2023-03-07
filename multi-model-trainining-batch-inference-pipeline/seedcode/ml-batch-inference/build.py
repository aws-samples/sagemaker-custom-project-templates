import argparse
import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

from pipelines import run_pipeline

import sagemaker
from sagemaker.model import Model
from sagemaker.pytorch import PyTorchModel
from sagemaker.utils import name_from_base
from sagemaker import get_execution_role

BASE_DIR = os.path.dirname(os.path.realpath(__file__))

logger = logging.getLogger(__name__)
sagemaker_client = boto3.client("sagemaker")
sagemaker_session = sagemaker.Session()


def get_approved_package(model_package_group_name):
    """Gets the latest approved model package for a model package group.

    Args:
        model_package_group_name: The model package group name.

    Returns:
        The SageMaker Model Package ARN.
    """
    try:
        # Get the latest approved model package
        response = sagemaker_client.list_model_packages(
            ModelPackageGroupName=model_package_group_name,
            ModelApprovalStatus="Approved",
            SortBy="CreationTime",
            SortOrder="Descending",
            MaxResults=1,
        )
        approved_packages = response["ModelPackageSummaryList"]

        # Return error if no packages found
        if len(approved_packages) == 0:
            error_message = ("No approved ModelPackage found for ModelPackageGroup: {}".format(model_package_group_name))
            print("{}".format(error_message))

            raise Exception(error_message)

        model_package = approved_packages[0]
        print("Identified the latest approved model package: {}".format(model_package))
        
        return model_package
    except ClientError as e:
        stacktrace = traceback.format_exc()
        error_message = e.response["Error"]["Message"]
        print("{}".format(stacktrace))

        raise Exception(error_message)

def describe_model_package(model_package_arn):
    try:
        model_package = sagemaker_client.describe_model_package(
            ModelPackageName=model_package_arn
        )

        print("{}".format(model_package))

        if len(model_package) == 0:
            error_message = ("No ModelPackage found for: {}".format(model_package_arn))
            print("{}".format(error_message))

            raise Exception(error_message)

        return model_package
    except ClientError as e:
        stacktrace = traceback.format_exc()
        error_message = e.response["Error"]["Message"]
        print("{}".format(stacktrace))

        raise Exception(error_message)
        
def extend_config(args, model_package_arn, pipeline_definitions, stage_config):
    """
    Extend the stage configuration with additional parameters and tags based.
    """
    # Verify that config has parameters and tags sections
    if not "Parameters" in stage_config or not "StageName" in stage_config["Parameters"]:
        raise Exception("Configuration file must include SageName parameter")
    if not "Tags" in stage_config:
        stage_config["Tags"] = {}
    # Create new params and tags
    new_params = {
        "SageMakerProjectName": args.sagemaker_project_name,
        "SageMakerProjectId": args.sagemaker_project_id,
        "ModelExecutionRoleArn": args.model_execution_role,
    }
    
    index = 1
    for pipeline_definition in pipeline_definitions:
        new_params["PipelineDefinitionBody" + str(index)] = pipeline_definition
        index +=1
    
    new_tags = {
        "sagemaker:deployment-stage": stage_config["Parameters"]["StageName"],
        "sagemaker:project-id": args.sagemaker_project_id,
        "sagemaker:project-name": args.sagemaker_project_name,
    }
    # Add tags from Project
    get_pipeline_custom_tags(args, sagemaker_client, new_tags)

    return {
        "Parameters": {**stage_config["Parameters"], **new_params},
        "Tags": {**stage_config.get("Tags", {}), **new_tags},
    }

def get_pipeline_custom_tags(args, sagemaker_client, new_tags):
    try:
        response = sagemaker_client.list_tags(
                ResourceArn=args.sagemaker_project_arn)
        project_tags = response["Tags"]
        for project_tag in project_tags:
            new_tags[project_tag["Key"]] = project_tag["Value"]
    except:
        logger.error("Error getting project tags")
    return new_tags

def get_cfn_style_config(stage_config):
    parameters = []
    for key, value in stage_config["Parameters"].items():
        parameter = {
            "ParameterKey": key,
            "ParameterValue": value
        }
        parameters.append(parameter)
    tags = []
    for key, value in stage_config["Tags"].items():
        tag = {
            "Key": key,
            "Value": value
        }
        tags.append(tag)
    return parameters, tags

def create_cfn_params_tags_file(config, export_params_file, export_tags_file):
    # Write Params and tags in separate file for Cfn cli command
    parameters, tags = get_cfn_style_config(config)
    with open(export_params_file, "w") as f:
        json.dump(parameters, f, indent=4)
    with open(export_tags_file, "w") as f:
        json.dump(tags, f, indent=4)
        
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-level", type=str, default=os.environ.get("LOGLEVEL", "INFO").upper())
    parser.add_argument("--aws-region", type=str, required=True)
    parser.add_argument("--default-bucket", type=str, required=True)
    parser.add_argument("--model-execution-role", type=str, required=True)
    parser.add_argument("--model-package-group-names", type=str, required=True)
    parser.add_argument("--sagemaker-project-id", type=str, required=True)
    parser.add_argument("--sagemaker-project-name", type=str, required=True)
    parser.add_argument("--inference-framework-version", type=str, required=True)
    parser.add_argument("--inference-python-version", type=str, required=True)
    parser.add_argument("--sagemaker-project-arn", type=str, required=False)
    parser.add_argument("--import-staging-config", type=str, default="staging-config.json")
    parser.add_argument("--import-prod-config", type=str, default="prod-config.json")
    parser.add_argument("--export-staging-config", type=str, default="staging-config-export.json")
    parser.add_argument("--export-staging-params", type=str, default="staging-params-export.json")
    parser.add_argument("--export-staging-tags", type=str, default="staging-tags-export.json")
    parser.add_argument("--export-prod-config", type=str, default="prod-config-export.json")
    parser.add_argument("--export-prod-params", type=str, default="prod-params-export.json")
    parser.add_argument("--export-prod-tags", type=str, default="prod-tags-export.json")
    parser.add_argument("--export-cfn-params-tags", type=bool, default=False)
    parser.add_argument("--inference-instance-type", type=str, default="ml.m5.large")
    parser.add_argument("--inference-instance-count", type=str, default=1)
    args, _ = parser.parse_known_args()

    # Configure logging to output the line number and message
    log_format = "%(levelname)s: [%(filename)s:%(lineno)s] %(message)s"
    logging.basicConfig(format=log_format, level=args.log_level)
    
    model_names = []
    pipeline_definitions = []
    
    for model_package_group_name in args.model_package_group_names.split(","):
        logger.info("Model Package Group: {}".format(model_package_group_name))
        # Get the latest approved package
        model_package = get_approved_package(model_package_group_name)
        model_package_arn = model_package["ModelPackageArn"]

        model_package = describe_model_package(model_package_arn)
    
        model = PyTorchModel(
            entry_point=os.path.join(BASE_DIR, "pipelines", "batch_inference", "inference.py"),
            name=model_package_group_name + "-" + str(model_package["ModelPackageVersion"]),
            framework_version=str(args.inference_framework_version),
            py_version=args.inference_python_version,
            model_data=model_package["InferenceSpecification"]["Containers"][0]["ModelDataUrl"],
            role=args.model_execution_role,
            sagemaker_session=sagemaker_session
        )

        model.create(
            instance_type=args.inference_instance_type
        )
        
        model_names.append(model_package_group_name + "-" + str(model_package["ModelPackageVersion"]))
    
    # Build the pipeline
    pipeline_definition = run_pipeline.main(
        'pipelines.batch_inference.pipeline',
        args.model_execution_role,
        json.dumps([
            {"Key":"sagemaker:project-name","Value":args.sagemaker_project_name},
            {"Key":"sagemaker:project-id","Value":args.sagemaker_project_id}
        ]),
        json.dumps({
            'region':args.aws_region,
            'default_bucket':args.default_bucket,
            'model_names':model_names,
            'inference_instance_type':args.inference_instance_type,
            'inference_instance_count':args.inference_instance_count
        })
    )

    pipeline_definitions.append(pipeline_definition)

    # Write the staging config
    with open(args.import_staging_config, "r") as f:
        staging_config = extend_config(args, model_package_arn, pipeline_definitions, json.load(f))
    logger.debug("Staging config: {}".format(json.dumps(staging_config, indent=4)))
    with open(args.export_staging_config, "w") as f:
        json.dump(staging_config, f, indent=4)
    if (args.export_cfn_params_tags):
      create_cfn_params_tags_file(staging_config, args.export_staging_params, args.export_staging_tags)

    # Write the prod config for code pipeline
    with open(args.import_prod_config, "r") as f:
        prod_config = extend_config(args, model_package_arn, pipeline_definitions, json.load(f))
    logger.debug("Prod config: {}".format(json.dumps(prod_config, indent=4)))
    with open(args.export_prod_config, "w") as f:
        json.dump(prod_config, f, indent=4)
    if (args.export_cfn_params_tags):
      create_cfn_params_tags_file(prod_config, args.export_prod_params, args.export_prod_tags)

if __name__ == "__main__":
    main()