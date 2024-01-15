import argparse
import json
import logging
import os
import boto3
from botocore.exceptions import ClientError
from utils import upload_file_to_s3, get_cfn_style_config
import sys

sys.path.append(".")

from pipelines import run_pipeline

LOG_FORMAT = "%(levelname)s: [%(filename)s:%(lineno)s] %(message)s"
logger = logging.getLogger(__name__)

target_acc_boto3_session = boto3.Session(profile_name="target")
target_sm_client = target_acc_boto3_session.client("sagemaker")
target_s3_client = target_acc_boto3_session.client("s3")


def extend_config(script_args, static_config):
    """Extend the stage configuration with additional parameters. SageMaker Project details
    and Model details. This function should be extended as required to pass on other
    dynamic configurations.
    """
    new_params = {
        "SageMakerProjectName": script_args.sagemaker_project_name,
        "SageMakerProjectId": script_args.sagemaker_project_id,
        "ProjectBucket": target_bucket,
        "Environment": script_args.environment,
        "SubnetIds": subnets,
        "SGIds": security_group_ids,
        "BatchPipeline": batch_pipeline,
        "PipelineDefinitionS3Key": s3_key_pipeline,
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
    parser.add_argument("--environment", type=str, required=True)
    parser.add_argument("--region", type=str, required=True)
    parser.add_argument("--target-id", type=str, required=True)
    parser.add_argument("--import-config", type=str, required=True)
    parser.add_argument("--export-config", type=str, required=True)
    parser.add_argument("--pipeline-file", type=str, default="pipelinedefinition.json")
    parser.add_argument("--code", type=str, required=True)  # tf or cfn

    args, _ = parser.parse_known_args()

    # Configure logging to output the line number and message
    logging.basicConfig(format=LOG_FORMAT, level=args.log_level)

    # get target bucket, subnets and sg group from ssm
    ssm = boto3.client("ssm")
    target_bucket = ssm.get_parameter(
        Name=f"/{args.environment}/sagemaker_ml_artifacts_s3_bucket"
    )["Parameter"]["Value"]
    sagemaker_role_arn = ssm.get_parameter(
        Name=f"/{args.environment}/sagemaker_role_arn"
    )["Parameter"]["Value"]

    security_group_ids = ssm.get_parameter(
        Name=f"/{args.environment}/sagemaker-domain-sg"
    )["Parameter"]["Value"]
    subnets = ssm.get_parameter(Name=f"/{args.environment}/private-subnets-ids")[
        "Parameter"
    ]["Value"]
    batch_pipeline = f"{args.sagemaker_project_name}-{args.sagemaker_project_id}-{args.stage}-pipeline"

    # Build the pipeline
    pipeline_definition = run_pipeline.main_target(
        "pipelines.batch_inference.pipeline",
        json.dumps(
            {
                "region": args.region,
                "environment": args.environment,
                "account_id": args.target_id,
                "role": sagemaker_role_arn,
                "default_bucket": target_bucket,
                "pipeline_name": batch_pipeline,
                "base_job_prefix": f"{args.sagemaker_project_name}-{args.sagemaker_project_id}",
                "project_name": args.sagemaker_project_name,
                "model_package_group_name": args.model_package_group_name,
            }
        ),
    )
    logger.info(json.dumps(pipeline_definition, indent=4))

    # Upload pipeline definition on a json file and to s3
    pipeline_dct = json.loads(pipeline_definition)
    with open(f"{args.stage}-{args.pipeline_file}", "w") as f:
        f.write(json.dumps(pipeline_dct))
    s3_key_pipeline = f"{args.sagemaker_project_name}-{args.sagemaker_project_id}/pipeline/{args.stage}-{args.pipeline_file}"
    upload_path = f"s3://{target_bucket}/{s3_key_pipeline}"

    upload_file_to_s3(
        f"{args.stage}-{args.pipeline_file}", upload_path, target_s3_client
    )
    logger.info("Uploaded: %s to %s", f"{args.stage}-{args.pipeline_file}", upload_path)

    # Extend the config file
    with open(args.import_config, "r", encoding="utf-8") as f:
        config = json.load(f)

    extended_config = extend_config(
        args,
        config,
    )
    with open(args.export_config, "w", encoding="utf-8") as f:
        json.dump(extended_config, f, indent=4)
