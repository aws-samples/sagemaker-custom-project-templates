"""Example workflow pipeline script for abalone pipeline.

                                               . -ModelStep
                                              .
    Process-> Train -> Evaluate -> Condition .
                                              .
                                               . -(stop)

Implements a get_pipeline(**kwargs) method.

Uses the SageMaker Python SDK v3 API:
- ModelTrainer (replaces Estimator)
- ScriptProcessor from sagemaker.core.processing
- ModelBuilder from sagemaker.serve
- Pipeline/steps from sagemaker.mlops.workflow
"""
import os

import boto3

from sagemaker.train.model_trainer import ModelTrainer
from sagemaker.core.training.configs import SourceCode, Compute, InputData, OutputDataConfig
from sagemaker.core.processing import FrameworkProcessor
from sagemaker.core.shapes import (
    ProcessingInput,
    ProcessingS3Input,
    ProcessingOutput,
    ProcessingS3Output,
)
from sagemaker.serve.model_builder import ModelBuilder
from sagemaker.core.workflow.parameters import (
    ParameterInteger,
    ParameterString,
)
from sagemaker.mlops.workflow.pipeline import Pipeline
from sagemaker.mlops.workflow.steps import ProcessingStep, TrainingStep, CacheConfig
from sagemaker.mlops.workflow.model_step import ModelStep
from sagemaker.mlops.workflow.condition_step import ConditionStep
from sagemaker.core.workflow.conditions import ConditionLessThanOrEqualTo
from sagemaker.core.workflow.functions import JsonGet
from sagemaker.core.workflow.properties import PropertyFile
from sagemaker.core.workflow.pipeline_context import PipelineSession
from sagemaker.core.helper.session_helper import Session, get_execution_role
from sagemaker.core import image_uris
from sagemaker.core.model_metrics import MetricsSource, ModelMetrics


BASE_DIR = os.path.dirname(os.path.realpath(__file__))

# Workaround for SDK v3 bug: get_training_code_hash expects dependencies to be a list,
# but SourceCode.requirements is a str or None. Patch it to handle both cases.
def _patch_training_code_hash():
    from sagemaker.core.workflow import utilities
    _original = utilities.get_training_code_hash

    def _patched(entry_point, source_dir, dependencies):
        if dependencies is None:
            dependencies = []
        elif isinstance(dependencies, str):
            dependencies = [dependencies]
        return _original(entry_point, source_dir, dependencies)

    utilities.get_training_code_hash = _patched

_patch_training_code_hash()


def get_sagemaker_client(region):
    """Gets the sagemaker client.

    Args:
        region: the aws region to start the session

    Returns:
        sagemaker client
    """
    boto_session = boto3.Session(region_name=region)
    return boto_session.client("sagemaker")


def get_session(region, default_bucket):
    """Gets the sagemaker session based on the region.

    Args:
        region: the aws region to start the session
        default_bucket: the bucket to use for storing the artifacts

    Returns:
        Session instance
    """
    boto_session = boto3.Session(region_name=region)
    sagemaker_client = boto_session.client("sagemaker")
    runtime_client = boto_session.client("sagemaker-runtime")
    return Session(
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
    except Exception as e:
        print(f"Error getting project tags: {e}")
    return new_tags


def get_pipeline(
    region,
    sagemaker_project_arn=None,
    role=None,
    default_bucket=None,
    model_package_group_name="AbalonePackageGroup",
    pipeline_name="AbalonePipeline",
    base_job_prefix="Abalone",
    processing_instance_type="ml.m5.xlarge",
    training_instance_type="ml.m5.xlarge",
    mlflow_tracking_arn="",
):
    """Gets a SageMaker ML Pipeline instance working with on abalone data.

    Args:
        region: AWS region to create and run the pipeline.
        role: IAM role to create and run steps and pipeline.
        default_bucket: the bucket to use for storing the artifacts
        mlflow_tracking_arn: Optional ARN of SageMaker managed MLflow Tracking Server.
            When provided, MLflow autologging is enabled for the training step.

    Returns:
        an instance of a pipeline
    """
    sagemaker_session = get_session(region, default_bucket)
    if role is None:
        role = get_execution_role(sagemaker_session)

    pipeline_session = get_pipeline_session(region, default_bucket)

    # parameters for pipeline execution
    processing_instance_count = ParameterInteger(name="ProcessingInstanceCount", default_value=1)
    model_approval_status = ParameterString(
        name="ModelApprovalStatus", default_value="PendingManualApproval"
    )
    input_data = ParameterString(
        name="InputDataUrl",
        default_value=f"s3://sagemaker-servicecatalog-seedcode-{region}/dataset/abalone-dataset.csv",
    )

    cache_config = CacheConfig(enable_caching=True, expire_after="30d")

    # --- MLflow environment variables ---
    # When MLflow is enabled, pass tracking config to all pipeline steps.
    # Each execution gets a unique experiment name (pipeline name + timestamp)
    # so all step runs are grouped per execution in the MLflow UI.
    mlflow_env = {}
    if mlflow_tracking_arn:
        from datetime import datetime, timezone

        execution_ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        experiment_name = f"{pipeline_name}/{execution_ts}"
        mlflow_env = {
            "MLFLOW_TRACKING_ARN": mlflow_tracking_arn,
            "MLFLOW_EXPERIMENT_NAME": experiment_name,
        }

    # --- Processing Step ---
    sklearn_image_uri = image_uris.retrieve(
        framework="sklearn",
        region=region,
        version="1.2-1",
        py_version="py3",
        instance_type=processing_instance_type,
    )
    sklearn_processor = FrameworkProcessor(
        image_uri=sklearn_image_uri,
        instance_type=processing_instance_type,
        instance_count=processing_instance_count,
        base_job_name=f"{base_job_prefix}/sklearn-abalone-preprocess",
        sagemaker_session=pipeline_session,
        role=role,
        env=mlflow_env if mlflow_env else None,
    )
    step_process_args = sklearn_processor.run(
        code="preprocess.py",
        source_dir=BASE_DIR,
        outputs=[
            ProcessingOutput(
                output_name="train",
                s3_output=ProcessingS3Output(
                    s3_uri=f"s3://{default_bucket}/{base_job_prefix}/train",
                    local_path="/opt/ml/processing/train",
                    s3_upload_mode="EndOfJob",
                ),
            ),
            ProcessingOutput(
                output_name="validation",
                s3_output=ProcessingS3Output(
                    s3_uri=f"s3://{default_bucket}/{base_job_prefix}/validation",
                    local_path="/opt/ml/processing/validation",
                    s3_upload_mode="EndOfJob",
                ),
            ),
            ProcessingOutput(
                output_name="test",
                s3_output=ProcessingS3Output(
                    s3_uri=f"s3://{default_bucket}/{base_job_prefix}/test",
                    local_path="/opt/ml/processing/test",
                    s3_upload_mode="EndOfJob",
                ),
            ),
        ],
        arguments=["--input-data", input_data],
    )
    step_process = ProcessingStep(
        name="PreprocessAbaloneData",
        step_args=step_process_args,
        cache_config=cache_config,
    )

    # --- Training Step (XGBoost script mode via ModelTrainer) ---
    model_path = f"s3://{default_bucket}/{base_job_prefix}/AbaloneTrain"

    xgb_image_uri = image_uris.retrieve(
        framework="xgboost",
        region=region,
        version="1.7-1",
        py_version="py3",
        instance_type=training_instance_type,
    )

    model_trainer = ModelTrainer(
        training_image=xgb_image_uri,
        source_code=SourceCode(
            source_dir=BASE_DIR,
            entry_script="train.py",
        ),
        compute=Compute(
            instance_type=training_instance_type,
            instance_count=1,
        ),
        hyperparameters={
            "objective": "reg:linear",
            "num_round": 50,
            "max_depth": 5,
            "eta": 0.2,
            "gamma": 4,
            "min_child_weight": 7,
            "subsample": 0.7,
        },
        output_data_config=OutputDataConfig(s3_output_path=model_path),
        base_job_name=f"{base_job_prefix}/abalone-train",
        sagemaker_session=pipeline_session,
        role=role,
        environment=mlflow_env if mlflow_env else None,
    )
    train_args = model_trainer.train(
        input_data_config=[
            InputData(
                channel_name="train",
                data_source=step_process.properties.ProcessingOutputConfig.Outputs[
                    "train"
                ].S3Output.S3Uri,
                content_type="text/csv",
            ),
            InputData(
                channel_name="validation",
                data_source=step_process.properties.ProcessingOutputConfig.Outputs[
                    "validation"
                ].S3Output.S3Uri,
                content_type="text/csv",
            ),
        ],
    )
    step_train = TrainingStep(
        name="TrainAbaloneModel",
        step_args=train_args,
        cache_config=cache_config,
    )

    # --- Evaluation Step ---
    script_eval = FrameworkProcessor(
        image_uri=xgb_image_uri,
        command=["python3"],
        instance_type=processing_instance_type,
        instance_count=1,
        base_job_name=f"{base_job_prefix}/script-abalone-eval",
        sagemaker_session=pipeline_session,
        role=role,
        env=mlflow_env if mlflow_env else None,
    )
    step_eval_args = script_eval.run(
        code="evaluate.py",
        source_dir=BASE_DIR,
        inputs=[
            ProcessingInput(
                input_name="model",
                s3_input=ProcessingS3Input(
                    s3_uri=step_train.properties.ModelArtifacts.S3ModelArtifacts,
                    local_path="/opt/ml/processing/model",
                    s3_data_type="S3Prefix",
                    s3_input_mode="File",
                ),
            ),
            ProcessingInput(
                input_name="test",
                s3_input=ProcessingS3Input(
                    s3_uri=step_process.properties.ProcessingOutputConfig.Outputs[
                        "test"
                    ].S3Output.S3Uri,
                    local_path="/opt/ml/processing/test",
                    s3_data_type="S3Prefix",
                    s3_input_mode="File",
                ),
            ),
        ],
        outputs=[
            ProcessingOutput(
                output_name="evaluation",
                s3_output=ProcessingS3Output(
                    s3_uri=f"s3://{default_bucket}/{base_job_prefix}/evaluation",
                    local_path="/opt/ml/processing/evaluation",
                    s3_upload_mode="EndOfJob",
                ),
            ),
        ],
    )
    evaluation_report = PropertyFile(
        name="AbaloneEvaluationReport",
        output_name="evaluation",
        path="evaluation.json",
    )
    step_eval = ProcessingStep(
        name="EvaluateAbaloneModel",
        step_args=step_eval_args,
        property_files=[evaluation_report],
        cache_config=cache_config,
    )

    # --- Model Registration Step ---
    model_metrics = ModelMetrics(
        model_statistics=MetricsSource(
            s3_uri="{}/evaluation.json".format(
                step_eval.arguments["ProcessingOutputConfig"]["Outputs"][0]["S3Output"]["S3Uri"]
            ),
            content_type="application/json",
        )
    )
    model_builder = ModelBuilder(
        s3_model_data_url=step_train.properties.ModelArtifacts.S3ModelArtifacts,
        image_uri=xgb_image_uri,
        sagemaker_session=pipeline_session,
        role_arn=role,
    )
    step_register = ModelStep(
        name="RegisterAbaloneModel",
        step_args=model_builder.register(
            model_package_group_name=model_package_group_name,
            content_types=["text/csv"],
            response_types=["text/csv"],
            inference_instances=["ml.t2.medium", "ml.m5.large"],
            transform_instances=["ml.m5.large"],
            approval_status=model_approval_status,
            model_metrics=model_metrics,
        ),
    )

    # --- Condition Step ---
    cond_lte = ConditionLessThanOrEqualTo(
        left=JsonGet(
            step_name=step_eval.name,
            property_file=evaluation_report,
            json_path="regression_metrics.mse.value",
        ),
        right=6.0,
    )
    step_cond = ConditionStep(
        name="CheckMSEAbaloneEvaluation",
        conditions=[cond_lte],
        if_steps=[step_register],
        else_steps=[],
    )

    # --- Pipeline ---
    pipeline = Pipeline(
        name=pipeline_name,
        parameters=[
            processing_instance_count,
            training_instance_type,
            model_approval_status,
            input_data,
        ],
        steps=[step_process, step_train, step_eval, step_cond],
        sagemaker_session=pipeline_session,
    )
    return pipeline