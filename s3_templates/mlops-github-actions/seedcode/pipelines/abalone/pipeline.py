"""Abalone pipeline using @step decorator with MLflow parent/child run tracking.

                                               . -RegisterStep
                                              .
    Preprocess -> Train -> Evaluate -> Cond .
                                              .
                                               . -(Fail)

The preprocessing step creates the MLflow parent run. All subsequent steps
resume it and create nested child runs, so the MLflow UI shows a single
tree per pipeline execution.

Implements a get_pipeline(**kwargs) method.
"""
import boto3

from sagemaker.core.workflow.parameters import ParameterString
from sagemaker.mlops.workflow.pipeline import Pipeline
from sagemaker.mlops.workflow.condition_step import ConditionStep
from sagemaker.core.workflow.conditions import ConditionLessThanOrEqualTo
from sagemaker.mlops.workflow.fail_step import FailStep
from sagemaker.core.workflow.execution_variables import ExecutionVariables

from pipelines.abalone.steps.processing import build_preprocess_step
from pipelines.abalone.steps.train import build_train_step
from pipelines.abalone.steps.evaluate import build_evaluate_step
from pipelines.abalone.steps.register import build_register_step


def get_sagemaker_client(region):
    boto_session = boto3.Session(region_name=region)
    return boto_session.client("sagemaker")


def get_pipeline_custom_tags(new_tags, region, sagemaker_project_arn=None):
    try:
        sm_client = get_sagemaker_client(region)
        response = sm_client.list_tags(ResourceArn=sagemaker_project_arn)
        for tag in response["Tags"]:
            new_tags.append(tag)
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
    """Gets a SageMaker ML Pipeline instance using @step decorators with MLflow tracking.

    Args:
        region: AWS region to create and run the pipeline.
        role: IAM role to create and run steps and pipeline.
        default_bucket: the bucket to use for storing the artifacts.
        mlflow_tracking_arn: Optional ARN of SageMaker managed MLflow Tracking Server.

    Returns:
        an instance of a pipeline
    """
    from sagemaker.core.helper.session_helper import Session, get_execution_role
    from sagemaker.core import image_uris

    boto_session = boto3.Session(region_name=region)
    sagemaker_client = boto_session.client("sagemaker")
    runtime_client = boto_session.client("sagemaker-runtime")
    sagemaker_session = Session(
        boto_session=boto_session,
        sagemaker_client=sagemaker_client,
        sagemaker_runtime_client=runtime_client,
        default_bucket=default_bucket,
    )
    if role is None:
        role = get_execution_role(sagemaker_session)

    # Pipeline parameters
    instance_type = ParameterString(name="InstanceType", default_value=training_instance_type)
    input_data = ParameterString(
        name="InputDataUrl",
        default_value=f"s3://sagemaker-servicecatalog-seedcode-{region}/dataset/abalone-dataset.csv",
    )

    tracking_arn = mlflow_tracking_arn or ""

    # XGBoost image URI for model registration
    xgb_image_uri = image_uris.retrieve(
        framework="xgboost",
        region=region,
        version="1.7-1",
        py_version="py3",
        instance_type=training_instance_type,
    )

    # --- Build step functions ---
    preprocess = build_preprocess_step(instance_type)
    train = build_train_step(instance_type)
    evaluate = build_evaluate_step(instance_type)
    register = build_register_step(instance_type)

    # --- Wire steps ---
    preprocessing_result = preprocess(
        raw_data_s3_path=input_data,
        output_bucket=default_bucket,
        output_prefix=f"{base_job_prefix}/dataset",
        experiment_name=pipeline_name,
        run_name=ExecutionVariables.PIPELINE_EXECUTION_ID,
        tracking_arn=tracking_arn,
    )

    training_result = train(
        train_s3_path=preprocessing_result[0],
        validation_s3_path=preprocessing_result[1],
        experiment_name=preprocessing_result[3],
        run_id=preprocessing_result[4],
        tracking_arn=tracking_arn,
    )

    eval_result = evaluate(
        test_s3_path=preprocessing_result[2],
        experiment_name=preprocessing_result[3],
        run_id=preprocessing_result[4],
        training_run_id=training_result[2],
        tracking_arn=tracking_arn,
    )

    conditional_register = ConditionStep(
        name="CheckMSEAbaloneEvaluation",
        conditions=[
            ConditionLessThanOrEqualTo(
                left=eval_result["mse"],
                right=6.0,
            )
        ],
        if_steps=[
            register(
                model_package_group_name=model_package_group_name,
                model_s3_uri=training_result[4],
                image_uri=xgb_image_uri,
            )
        ],
        else_steps=[
            FailStep(
                name="ModelQualityFail",
                error_message="Model MSE exceeds threshold (6.0)",
            )
        ],
    )

    # --- Pipeline ---
    pipeline = Pipeline(
        name=pipeline_name,
        parameters=[instance_type, input_data],
        steps=[preprocessing_result, training_result, conditional_register],
        sagemaker_session=sagemaker_session,
    )
    return pipeline