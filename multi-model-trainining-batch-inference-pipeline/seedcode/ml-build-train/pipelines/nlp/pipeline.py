import boto3
import json
import logging
import os
import sagemaker
from sagemaker.inputs import TrainingInput
from sagemaker.processing import FrameworkProcessor, ProcessingInput, ProcessingOutput
import sagemaker.session
from sagemaker.pytorch import PyTorch
from sagemaker.sklearn.estimator import SKLearn
from sagemaker.workflow.parameters import ParameterFloat, ParameterInteger, ParameterString
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.pipeline_context import PipelineSession
from sagemaker.workflow.step_collections import RegisterModel
from sagemaker.workflow.steps import ProcessingStep, TrainingStep
import traceback

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
    sagemaker_project_arn=None,
    role=None,
    default_bucket=None,
    model_package_group_name_1="NlpPackageGroup-1",
    model_package_group_name_2="NlpModelPackageGroup-2",
    pipeline_name="NlpPipeline",
    base_job_prefix="Nlp",
    processing_instance_type="ml.t3.large",
    training_instance_type="ml.m5.large",
    inference_instance_type="ml.m5.large"
):
    pipeline_session = get_pipeline_session(region, default_bucket)
    
    if role is None:
        role = sagemaker.session.get_execution_role(pipeline_session)

    input_data = ParameterString(
        name="InputData", default_value="s3://{}/datasets/tabular/tweets_dataset".format(default_bucket)
    )

    model_approval_status = ParameterString(
        name="ModelApprovalStatus", default_value="PendingManualApproval"
    )

    processing_instance_count_param= ParameterInteger(
        name="ProcessingInstanceCount", default_value=1
    )

    training_instance_count_param= ParameterInteger(
        name="TrainingInstanceCount", default_value=1
    )
    
    processing_framework_version = "0.23-1"
    processing_output_files_path = "e2e-base/data/output"
    
    processor = FrameworkProcessor(
        estimator_cls=SKLearn,
        framework_version=processing_framework_version,
        role=role,
        instance_count=processing_instance_count_param,
        instance_type=processing_instance_type,
        sagemaker_session=pipeline_session
    )
    
    run_args = processor.get_run_args(
        code=os.path.join(BASE_DIR, "processing.py"),
        inputs=[
            ProcessingInput(
                input_name="input",
                source=input_data,
                destination="/opt/ml/processing/input"
            )
        ],
        outputs=[
            ProcessingOutput(
                output_name="train",
                source="/opt/ml/processing/output/train",
                destination="s3://{}/{}/train".format(default_bucket, processing_output_files_path)),
            ProcessingOutput(
                output_name="test",
                source="/opt/ml/processing/output/test",
                destination="s3://{}/{}/test".format(default_bucket, processing_output_files_path))
        ]
    )
    
    step_process = ProcessingStep(
        name="ProcessData",
        code=run_args.code,
        processor=processor,
        inputs=run_args.inputs,
        outputs=run_args.outputs
    )
    
    training_output_files_path = "e2e-base/models"
    training_framework_version = "1.12"
    training_python_version = "py38"
    training_hyperparameters = {
        "epochs": 25,
        "learning_rate": 0.001,
        "batch_size": 100
    }
    
    estimator_1 = PyTorch(
        os.path.join(BASE_DIR, "train_model_1.py"),
        framework_version=training_framework_version,
        py_version=training_python_version,
        output_path="s3://{}/{}".format(default_bucket,
                                        training_output_files_path),
        hyperparameters=training_hyperparameters,
        role=role,
        instance_count=training_instance_count_param,
        instance_type=training_instance_type,
        disable_profiler=True
    )
    
    step_train_1 = TrainingStep(
        depends_on=[step_process],
        name="TrainModel1",
        estimator=estimator_1,
        inputs={
            "train": TrainingInput(
                s3_data=step_process.properties.ProcessingOutputConfig.Outputs["train"].S3Output.S3Uri,
                content_type="text/csv"
            ),
            "test": TrainingInput(
                s3_data=step_process.properties.ProcessingOutputConfig.Outputs["test"].S3Output.S3Uri,
                content_type="text/csv"
            )
        }
    )
    
    estimator_2 = PyTorch(
        os.path.join(BASE_DIR, "train_model_2.py"),
        framework_version=training_framework_version,
        py_version=training_python_version,
        output_path="s3://{}/{}".format(default_bucket,
                                        training_output_files_path),
        hyperparameters=training_hyperparameters,
        role=role,
        instance_count=training_instance_count_param,
        instance_type=training_instance_type,
        disable_profiler=True
    )
    
    step_train_2 = TrainingStep(
        depends_on=[step_process],
        name="TrainModel2",
        estimator=estimator_2,
        inputs={
            "train": TrainingInput(
                s3_data=step_process.properties.ProcessingOutputConfig.Outputs["train"].S3Output.S3Uri,
                content_type="text/csv"
            ),
            "test": TrainingInput(
                s3_data=step_process.properties.ProcessingOutputConfig.Outputs["test"].S3Output.S3Uri,
                content_type="text/csv"
            )
        }
    )
    
    step_register_model_1 = RegisterModel(
        name="RegisterModel1",
        estimator=estimator_1,
        model_data=step_train_1.properties.ModelArtifacts.S3ModelArtifacts,
        model_package_group_name=model_package_group_name_1,
        approval_status=model_approval_status,
        content_types=["text/csv"],
        response_types=["text/csv"],
        inference_instances=[inference_instance_type],
        transform_instances=[inference_instance_type]
    )
    
    step_register_model_2 = RegisterModel(
        name="RegisterModel2",
        estimator=estimator_2,
        model_data=step_train_2.properties.ModelArtifacts.S3ModelArtifacts,
        model_package_group_name=model_package_group_name_2,
        approval_status=model_approval_status,
        content_types=["text/csv"],
        response_types=["text/csv"],
        inference_instances=[inference_instance_type],
        transform_instances=[inference_instance_type]
    )
    
    pipeline = Pipeline(
        name=pipeline_name,
        parameters=[
            input_data,
            model_approval_status,
            processing_instance_count_param,
            training_instance_count_param
        ],
        steps=[
            step_process,
            step_train_1, 
            step_register_model_1,
            step_train_2, 
            step_register_model_2
        ],
        sagemaker_session=pipeline_session
    )
    
    return pipeline