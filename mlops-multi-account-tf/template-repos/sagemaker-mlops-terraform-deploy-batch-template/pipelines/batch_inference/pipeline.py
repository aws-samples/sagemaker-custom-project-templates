"""Example workflow Batch inference pipeline script for abalone pipeline.


    Process-> Inference

Implements a get_pipeline(**kwargs) method.
"""
import os

import boto3
import sagemaker
import sagemaker.session

from sagemaker.transformer import Transformer
from sagemaker.processing import (
    ProcessingInput,
    ProcessingOutput,
    ScriptProcessor,
)
from sagemaker.inputs import TransformInput

from sagemaker.workflow.parameters import (
    ParameterInteger,
    ParameterString,
)
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.properties import PropertyFile
from sagemaker.workflow.steps import (
    ProcessingStep,
    TransformStep,
)

from sagemaker.workflow.pipeline_context import PipelineSession
from sagemaker.network import NetworkConfig


BASE_DIR = os.path.dirname(os.path.realpath(__file__))


def get_sagemaker_client(region):
    """Gets the sagemaker client.

    Args:
        region: the aws region to start the session
        default_bucket: the bucket to use for storing the artifacts

    Returns:
        `sagemaker.session.Session instance
    """
    boto_session = boto3.Session(region_name=region)
    return boto_session.client("sagemaker")


def get_session(region, default_bucket):
    """Gets the sagemaker session based on the region.

    Args:
        region: the aws region to start the session
        default_bucket: the bucket to use for storing the artifacts

    Returns:
        `sagemaker.session.Session instance
    """

    boto_session = boto3.Session(region_name=region)

    sagemaker_client = boto_session.client("sagemaker")
    runtime_client = boto_session.client("sagemaker-runtime")
    return sagemaker.session.Session(
        boto_session=boto_session,
        sagemaker_client=sagemaker_client,
        sagemaker_runtime_client=runtime_client,
        default_bucket=default_bucket,
    )


def get_pipeline_session(region, default_bucket):
    """Gets the pipeline session based on the region.

    Args:
        region: the aws region to start the session
        default_bucket: the bucket to use for storing the artifacts

    Returns:
        PipelineSession instance
    """

    boto_session = boto3.Session(region_name=region)
    sagemaker_client = boto_session.client("sagemaker")

    return PipelineSession(
        boto_session=boto_session,
        sagemaker_client=sagemaker_client,
        default_bucket=default_bucket,
    )


def get_pipeline_custom_tags(new_tags, region, sagemaker_project_arn=None):
    try:
        sm_client = get_sagemaker_client(region)
        response = sm_client.list_tags(ResourceArn=sagemaker_project_arn)
        project_tags = response["Tags"]
        for project_tag in project_tags:
            new_tags.append(project_tag)
    except Exception as err:
        print(f"Error getting project tags: {err}")
    return new_tags


def get_pipeline(
    region,
    stage,  # staging o prod
    environment,  # preprod or prod
    account_id,
    role=None,
    default_bucket=None,
    pipeline_name="AbalonePipeline",
    base_job_prefix="Abalone",
    project_name="SageMakerProjectName",
):
    """Gets a SageMaker ML Pipeline instance working with on abalone data.

    Args:
        region: AWS region to create and run the pipeline.
        role: IAM role to create and run steps and pipeline.
        default_bucket: the bucket to use for storing the artifacts

    Returns:
        an instance of a pipeline
    """
    print(f"Role: {role}")
    sagemaker_session = get_session(region, default_bucket)
    if role is None:
        role = sagemaker.session.get_execution_role(sagemaker_session)

    pipeline_session = get_pipeline_session(region, default_bucket)
    ecr = boto3.client("ecr")
    # get VPC parameters from Parameter store
    ssm = boto3.client("ssm")
    security_group_ids = ssm.get_parameter(Name=f"sagemaker-domain-sg")["Parameter"][
        "Value"
    ].split(",")
    subnets = ssm.get_parameter(Name=f"private-subnets-ids")["Parameter"][
        "Value"
    ].split(",")
    # parameters for pipeline execution
    processing_instance_count = ParameterInteger(
        name="ProcessingInstanceCount", default_value=1
    )
    processing_instance_type = ParameterString(
        name="ProcessingInstanceType", default_value="ml.m5.xlarge"
    )

    inference_instance_count = ParameterInteger(
        name="InferenceInstanceCount", default_value=1
    )
    inference_instance_type = ParameterString(
        name="InferenceInstanceType", default_value="ml.m5.xlarge"
    )
    model_name = ParameterString(name="ModelName", default_value="Abalone")

    input_data = ParameterString(
        name="InputDataUrl",
        default_value=f"s3://sagemaker-servicecatalog-seedcode-{region}"
        "/dataset/abalone-dataset.csv",
    )
    # configure network for encryption, network isolation and VPC configuration
    network_config = NetworkConfig(
        enable_network_isolation=False,
        security_group_ids=security_group_ids,
        subnets=subnets,
        encrypt_inter_container_traffic=True,
    )
    # Parameters custom imagename convenction

    processing_image_name = "mlops-{0}-processing-{1}".format(project_name, stage)

    # processing step for feature engineering
    # try if exists custom image, else use bre built-image
    try:
        ecr.describe_images(
            repositoryName=processing_image_name, imageIds=[{"imageTag": "latest"}]
        )

        processing_image_uri = f"{account_id}.dkr.ecr.{region}.amazonaws.com/{processing_image_name}:latest"
    except:
        processing_image_uri = sagemaker.image_uris.retrieve(
            framework="xgboost",
            region=region,
            version="1.0-1",
            py_version="py3",
            instance_type=processing_instance_type,
        )
    script_processor = ScriptProcessor(
        image_uri=processing_image_uri,
        instance_type=processing_instance_type,
        instance_count=processing_instance_count,
        base_job_name=f"{base_job_prefix}/sklearn-abalone-preprocess",
        command=["python3"],
        network_config=network_config,
        sagemaker_session=pipeline_session,
        role=role,
    )
    step_args = script_processor.run(
        outputs=[
            ProcessingOutput(
                output_name="inference", source="/opt/ml/processing/inference"
            ),
        ],
        code=os.path.join(BASE_DIR, "preprocess.py"),
        arguments=["--input-data", input_data],
    )
    step_process = ProcessingStep(
        name="PreprocessAbaloneData",
        step_args=step_args,
    )

    # Batch inference
    transform_output_folder = "batch-output-abalone"
    output_path = "s3://{}/{}".format(default_bucket, transform_output_folder)
    transformer_config = Transformer(
        model_name=model_name,
        instance_count=inference_instance_count,
        instance_type=inference_instance_type,
        accept="text/csv",
        sagemaker_session=PipelineSession(),
        assemble_with="Line",
        output_path=output_path,
    )

    step_transform = TransformStep(
        name="AbaloneTransform",
        transformer=transformer_config,
        inputs=TransformInput(
            data=step_process.properties.ProcessingOutputConfig.Outputs[
                "inference"
            ].S3Output.S3Uri,
            data_type="S3Prefix",
            content_type="text/csv",
            split_type="Line",
            join_source="Input",
        ),
    )

    # pipeline instance

    pipeline = Pipeline(
        name=pipeline_name,
        parameters=[
            processing_instance_count,
            inference_instance_count,
            processing_instance_type,
            inference_instance_type,
            model_name,
            input_data,
        ],
        steps=[step_process, step_transform],
        sagemaker_session=pipeline_session,
    )

    return pipeline
