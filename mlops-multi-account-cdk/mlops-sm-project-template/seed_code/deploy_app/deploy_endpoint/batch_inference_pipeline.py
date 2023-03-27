"""

    Pipeline definition of how to :
    - data preprocessing
    - model training
    - model quality calculation
    - model quality evaluation, if model MSE pass threhold, then:
        - model explainability metrics calculation
        - model bias metrics calcuation 
        - and model registration 
"""
import os

import boto3
import logging
import sagemaker
import sagemaker.session
from datetime import datetime

from sagemaker.processing import (
    ProcessingOutput,
    ScriptProcessor
)
from sagemaker.workflow.parameters import ParameterInteger, ParameterString
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import ProcessingStep, TransformInput, Transformer, TransformStep, CacheConfig
from sagemaker.workflow.pipeline_context import PipelineSession


from sagemaker.workflow.execution_variables import ExecutionVariables
from sagemaker.workflow.functions import Join


from sagemaker.workflow.parameters import (
    ParameterBoolean,
    ParameterInteger,
    ParameterString,
)

from sagemaker.model_monitor import DatasetFormat


logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOGLEVEL", "INFO"))

header_names = [
    "rings",
    "length",
    "diameter",
    "height",
    "whole_weight",
    "shucked_weight",
    "viscera_weight",
    "shell_weight",
    "sex_I",
    "sex_F",
    "sex_M"
]
label_column = "rings"

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
    session = sagemaker.session.Session(
        boto_session=boto_session,
        sagemaker_client=sagemaker_client,
        sagemaker_runtime_client=runtime_client,
        default_bucket=default_bucket,
    )

    return session

class AbaloneBatchTransformPipeline():
    '''
    contains SageMaker pipeline definition for batch inference. Include all steps defined in the pipeline.

    '''
    def __init__(self,
        model_name,
        region,
        role=None,
        default_bucket=None,
        bucket_kms_id=None,
        pipeline_name="AbalonePipeline",
        base_job_prefix="AbaloneTransform",
        project_id="SageMakerProjectId",
    ):
        logger.info('Initializing AbaloneBatchTransformPipeline')
        self.region = region
        self.model_name = model_name
        self.base_job_prefix = base_job_prefix
        self.bucket_kms_id = bucket_kms_id
        self.pipeline_name = pipeline_name

        self.sagemaker_session = get_session(region, default_bucket)
        self.default_bucket = self.sagemaker_session.default_bucket() if default_bucket is None else default_bucket
        if role is None:
            self.role = sagemaker.session.get_execution_role(self.sagemaker_session)
            logger.info('Initializing AbaloneBatchTransformPipeline with sagemaker execution role: {}'.format(self.role))
        else:
            self.role = role
            logger.info('Initializing AbaloneBatchTransformPipeline with role parameter: {}'.format(self.role))

        # parameters for pipeline execution
        self.processing_instance_count = ParameterInteger(name="ProcessingInstanceCount", default_value=1)
        self.processing_instance_type = ParameterString(name="ProcessingInstanceType", default_value="ml.m5.2xlarge")
        self.training_instance_type = ParameterString(name="TrainingInstanceType", default_value="ml.m5.4xlarge")
        self.inference_instance_type = ParameterString(name="InferenceInstanceType", default_value="ml.m5.large")
        self.input_data = ParameterString(
                name="InputDataUrl",
                default_value=f"s3://sagemaker-servicecatalog-seedcode-{region}/dataset/abalone-dataset.csv",
        )
        self.processing_image_name = "sagemaker-{0}-processingimagebuild".format(project_id)
        self.training_image_name = "sagemaker-{0}-trainingimagebuild".format(project_id)
        self.inference_image_name = "sagemaker-{0}-inferenceimagebuild".format(project_id)

        self.pipeline_session = PipelineSession()

    def get_output_path(self, step_name):
        '''
        helper function to standardize the output path for the pipeline steps as:
        - pipeline creation time
            - source script 
            - pipeline execution time
                - step name
                - step name

        Args:
            step_name: the name of the step to get the output path for
        '''
        base = f"s3://{self.default_bucket}/{self.pipeline_name}/{self.base_job_prefix}"
        ret = Join("/", values=[base, ExecutionVariables.START_DATETIME, step_name])

        return ret

    def get_process_step(self)->ProcessingStep:
        '''
        create the pre-processing step to be used in SageMaker pipeline. The step will
        - apply one-hot encoding to the categorical features
        - save the pre-processed data to the output path

        Returns:
            ProcessingStep: the pre-processing step to be used in SageMaker pipeline
        '''
        step_name = "preprocessing"
        try:
            processing_image_uri = self.sagemaker_session.sagemaker_client.describe_image_version(
                ImageName=self.processing_image_name
            )["ContainerImage"]
        except (self.sagemaker_session.sagemaker_client.exceptions.ResourceNotFound):
            processing_image_uri = sagemaker.image_uris.retrieve(
                framework="xgboost",
                region=self.region,
                version="1.0-1",
                py_version="py3"
            )
        script_processor = ScriptProcessor(
            image_uri=processing_image_uri,
            instance_type=self.processing_instance_type,
            instance_count=self.processing_instance_count,
            base_job_name=f"{self.pipeline_name}/{self.base_job_prefix}/{step_name}",
            command=["python3"],
            sagemaker_session=self.pipeline_session,
            role=self.role,
            output_kms_key=self.bucket_kms_id,
        )
        BASE_DIR = os.path.dirname(os.path.realpath(__file__))

        output_path = self.get_output_path(step_name)
        step_args = script_processor.run(
            # code = f"{BASE_DIR}/source_scripts/preprocessing/main.py",
            code = f"s3://{self.default_bucket}/{self.pipeline_name}/{self.base_job_prefix}/source-scripts/{step_name}/main.py",
            outputs=[ProcessingOutput(output_name="transform", source="/opt/ml/processing/output", destination=output_path)],
            arguments=["--input-data", self.input_data]
        )
        step_process = ProcessingStep(
            name=step_name,
            step_args=step_args,
            cache_config=CacheConfig(enable_caching=True, expire_after="T2H")
        )

        logger.info('Processing step created')
        return step_process
    

    def get_transform_step(self, step_process)->TransformStep:
        ''' 
        create a transform step to be used in SageMaker pipeline. The transform step will use the model to
        transform the test dataset
        
        Args:
            step_process: transform step depends on the process step
            step_create_model: transform step depends on the create model step
        Returns:
            TransformStep
        '''
        step_name = "transform"
        output_path = self.get_output_path(step_name)

        transform = Transformer(
            model_name=self.model_name,
            instance_count=1,
            instance_type=self.inference_instance_type,
            output_path=output_path,
            base_transform_job_name=f"{self.pipeline_name}/{step_name}",
            max_payload=10,
            accept='text/csv'
        )

        model_transform_step = TransformStep(
            name=step_name,
            transformer=transform,
            inputs=TransformInput(
                data=step_process.properties.ProcessingOutputConfig.Outputs["transform"].S3Output.S3Uri, 
                content_type='text/csv'
            )
        )
        logger.info('Transform step created')
        return model_transform_step


    def get_pipeline(self)->Pipeline:
        ''' 
        create a SageMaker pipeline to be used in SageMaker pipeline
        '''
        
        step_process = self.get_process_step()
        step_transform = self.get_transform_step(step_process)

        pipeline = Pipeline(
            name=self.pipeline_name,
            parameters=[
                self.processing_instance_type,
                self.processing_instance_count,
                self.inference_instance_type,
                self.input_data
            ],
            steps=[step_process, step_transform],
            sagemaker_session=self.sagemaker_session,
        )

        logger.info('Pipeline created')
        return pipeline


def get_pipeline(
    model_name,
    region='eu-west-1',
    role=None,
    default_bucket=None,
    bucket_kms_id=None,
    pipeline_name="AbalonePipeline",
    base_job_prefix="Abalone",
    project_id="SageMakerProjectId"
)->Pipeline:
    '''
    create a SageMaker pipeline:
    1. The pipeline will pre-process the data
    2. The pipeline will perform batch inference using SageMaker BatchTransform job

    Args:
        model_name: name of the model to be used in the pipeline
        region: region of the model to be used in the pipeline  
        role: pipeline's role to access data and inference
        default_bucket: default bucket to be used in the pipeline   
        bucket_kms_id: kms id when save data, make sure the kms_id is the same as S3's kms_id
        pipeline_name: name of the pipeline to be used in the pipeline  
        base_job_prefix: timestamp is a commonly used prefix for all jobs in the pipeline
        project_id: project id of the project to be used in the pipeline    
    Returns:
        Pipeline
    '''
    logger.info(f'Creating pipeline {pipeline_name=}, {base_job_prefix=}, {project_id=}')
    p = AbaloneBatchTransformPipeline(model_name, region, role, default_bucket, bucket_kms_id, pipeline_name, base_job_prefix, project_id)
    return p.get_pipeline()

