import os

import boto3
import sagemaker
from sagemaker import model
from sagemaker.pytorch import PyTorchModel
import sagemaker.session
from sagemaker.workflow.parameters import (
    ParameterInteger,
    ParameterString,
)
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.pipeline_context import PipelineSession
from sagemaker.workflow.steps import (
    TransformStep, 
    Transformer, 
    TransformInput
)

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
            ResourceArn=sagemaker_project_arn.lower())
        project_tags = response["Tags"]
        for project_tag in project_tags:
            new_tags.append(project_tag)
    except Exception as e:
        print(f"Error getting project tags: {e}")
    return new_tags

def get_pipeline(
    region,
    model_names,
    sagemaker_project_arn=None,
    role=None,
    default_bucket=None,
    pipeline_name="AbalonePipelineBatchInference",
    inference_instance_type="ml.m5.large",
    inference_instance_count=1
):
    """Gets a SageMaker ML Pipeline instance working with on abalone data.

    Args:
        region: AWS region to create and run the pipeline.
        model_name: Name of the SageMaker Model to deploy

    Returns:
        an instance of a pipeline
    """
    sagemaker_session = get_session(region, default_bucket)
    
    if role is None:
        role = sagemaker.session.get_execution_role(sagemaker_session)

    pipeline_session = get_pipeline_session(region, default_bucket)

    #### PARAMETERS
    model_url = ParameterString("ModelUrl")

    input_path = ParameterString("InputPath")
    output_path = ParameterString("OutputPath")
    
    transform_steps = []
    
    index = 1
    for model_name in model_names:
        
        transformer = Transformer(
            model_name=model_name,
            instance_count=inference_instance_count,
            instance_type=inference_instance_type,
            output_path=output_path,
            accept='text/csv',
            strategy='SingleRecord'
        )

        #### STEPS
        transform_step = TransformStep(
            name='BatchInferenceStep' + str(index),
            transformer=transformer,
            inputs=TransformInput(data=input_path, content_type='text/csv', split_type='Line')
        )
        
        transform_steps.append(transform_step)
        
        index +=1

    #### PIPELINE
    pipeline = Pipeline(
        name=pipeline_name,
        parameters=[input_path, output_path],
        steps=transform_steps,
        sagemaker_session=sagemaker_session
    )
    return pipeline
