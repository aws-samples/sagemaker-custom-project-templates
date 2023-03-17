# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# SPDX-License-Identifier: MIT-0
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""Example workflow pipeline script for batch transform pipeline.

    Create Model -> Transform Job

Implements a get_pipeline(**kwargs) method.
"""

import os
import time

import boto3
import logging
import sagemaker
import sagemaker.session

from sagemaker import ModelPackage
from sagemaker.inputs import TransformInput
from sagemaker.transformer import Transformer
from sagemaker.sklearn.processing import SKLearnProcessor
from sagemaker.processing import (
    ProcessingInput,
    ProcessingOutput
)
from sagemaker.workflow.execution_variables import ExecutionVariables
from sagemaker.workflow.functions import Join
from sagemaker.workflow.model_step import ModelStep
from sagemaker.workflow.steps import ProcessingStep, TransformStep
from sagemaker.workflow.parameters import ParameterInteger, ParameterString
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.pipeline_context import PipelineSession
from sagemaker.workflow.retry import (
    StepRetryPolicy, 
    StepExceptionTypeEnum,
    SageMakerJobExceptionTypeEnum,
    SageMakerJobStepRetryPolicy
)

# BASE_DIR = os.path.dirname(os.path.realpath(__file__))

logger = logging.getLogger(__name__)


def get_sagemaker_client(region):
    """Gets the sagemaker client.

    Args:
        region: the aws region to start the session

    Returns:
        `sagemaker.session.Session instance
    """
    boto_session = boto3.Session(region_name=region)
    sagemaker_client = boto_session.client("sagemaker")
    return sagemaker_client


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
        response = sm_client.list_tags(
            ResourceArn=sagemaker_project_arn)
        project_tags = response["Tags"]
        for project_tag in project_tags:
            new_tags.append(project_tag)
    except Exception as e:
        print(f"Error getting project tags: {e}")
    return new_tags

def get_pipeline(
    region,
    role,
    artifact_bucket,
    pipeline_name,
    base_job_prefix,
    model_package_arn,
    **kwargs
):
    """Gets a SageMaker ML Pipeline instance working with the data.

    Args:
        region: AWS region to create and run the pipeline.
        role: IAM role to create and run steps and pipeline.
        artifact_bucket: the bucket to use for storing the artifacts

    Returns:
        an instance of a pipeline
    """
    
    # For debugging
    # cache_config = CacheConfig(enable_caching=True, expire_after="1d")

    pipeline_session = get_pipeline_session(region, artifact_bucket)

    ############################################
    # Pipeline Parameters for pipeline execution
    ############################################
    processing_instance_type = ParameterString(
        name="ProcessingInstanceType",
        default_value="ml.m5.large"
    )
    processing_instance_count = ParameterInteger(
        name="ProcessingInstanceCount",
        default_value=1
    )
    transform_instance_type = ParameterString(
        name="TransformInstanceType",
        default_value="ml.m5.large"
    )
    transform_instance_count = ParameterInteger(
        name="TransformInstanceCount",
        default_value=1
    )

    input_data = ParameterString(
        name="InputDataUrl",
        default_value=f"s3://sagemaker-servicecatalog-seedcode-{region}/dataset/abalone-dataset.csv",
    )

    outputs_bucket = ParameterString(
        name="OutputsBucket"
    )

    # Retry policies
    # https://docs.aws.amazon.com/sagemaker/latest/dg/pipelines-retry-policy.html
    retry_policies=[
        # override the default 
        StepRetryPolicy(
            exception_types=[
                StepExceptionTypeEnum.SERVICE_FAULT, 
                StepExceptionTypeEnum.THROTTLING
            ],
            max_attempts=3,
            interval_seconds=10,
            backoff_rate=2.0,
        ),
         # retry when resource limit quota gets exceeded
        SageMakerJobStepRetryPolicy(
            exception_types=[SageMakerJobExceptionTypeEnum.RESOURCE_LIMIT],
            max_attempts=3,
            interval_seconds=60,
            backoff_rate=2.0
        ),
         # retry when job failed due to transient error or EC2 ICE.
        SageMakerJobStepRetryPolicy(
            failure_reason_types=[
                SageMakerJobExceptionTypeEnum.INTERNAL_ERROR,
                SageMakerJobExceptionTypeEnum.CAPACITY_ERROR,
            ],
            max_attempts=3,
            interval_seconds=30,
            backoff_rate=2.0
        )
    ]

    ############################################
    # Pipeline Steps definition
    ############################################
    
    # Create a model from latest model package in SM Model Registry
    model_package = ModelPackage(
        role=role, 
        model_package_arn=model_package_arn, 
        sagemaker_session=pipeline_session,
    )

    step_create_model = ModelStep(
        name="Create-model",
        step_args=model_package.create(instance_type=transform_instance_type),
    )
    
    # Processing step for feature engineering
    sklearn_processor = SKLearnProcessor(
        framework_version='0.20.0',
        instance_type=processing_instance_type,
        instance_count=processing_instance_count,
        base_job_name=f"{base_job_prefix}/sklearn-abalone-preprocess",
        sagemaker_session=pipeline_session,
        role=role,
    )
    step_process = ProcessingStep(
        name="PreprocessAbaloneData",
        processor=sklearn_processor,
        outputs=[
            ProcessingOutput(output_name="output_data", source="/opt/ml/processing/output_data"),
        ],
        code="source_scripts/preprocessing/prepare_abalone_data/main.py",  # we must figure out this path to get it from step_source directory
        job_arguments=[
            "--input-data", input_data,
            "--do-train-test-split", "False",
        ],
    )


    # Define qgen transformer and TransformStep
    output_transform = Join(on='/', values=['s3:/', outputs_bucket, base_job_prefix, ExecutionVariables.PIPELINE_EXECUTION_ID, "batch/"])

    transformer = Transformer(
        model_name=step_create_model.properties.ModelName,
        instance_count=transform_instance_count,
        instance_type=transform_instance_type,
        max_concurrent_transforms=64,
        max_payload=1,
        strategy = 'SingleRecord',
        assemble_with = 'Line',
        output_path=output_transform,
    )

    input_path_transform_step=step_process.properties.ProcessingOutputConfig.Outputs["output_data"].S3Output.S3Uri

    step_transformer = TransformStep(
        name="Transformer",
        transformer=transformer,
        inputs=TransformInput(
            data=input_path_transform_step,
            content_type= "text/csv",
            split_type = 'Line'
        ),
        retry_policies=retry_policies,
        # cache_config=cache_config
    )
    
    ############################################
    # Pipeline Definition
    ############################################
    pipeline = Pipeline(
        sagemaker_session=pipeline_session,
        name=pipeline_name,
        parameters=[
            input_data,
            outputs_bucket,
            transform_instance_count,
            transform_instance_type,
            processing_instance_count,
            processing_instance_type,
        ],
        steps=[
            step_create_model,
            step_process,
            step_transformer,
        ],
    )
    return pipeline
