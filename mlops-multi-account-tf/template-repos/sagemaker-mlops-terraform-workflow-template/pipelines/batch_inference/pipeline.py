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
from sagemaker.estimator import Estimator
from sagemaker.inputs import TrainingInput

from sagemaker.workflow.parameters import (
    ParameterInteger,
    ParameterString,
    ParameterFloat,
)
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.properties import PropertyFile
from sagemaker.workflow.steps import (
    ProcessingStep,
    TransformStep,
    TrainingStep,
)
from sagemaker.inputs import CreateModelInput
from sagemaker.workflow.model_step import ModelStep
from sagemaker.model import Model
from sagemaker.workflow.pipeline_context import PipelineSession
from sagemaker.network import NetworkConfig

from sagemaker.workflow.conditions import ConditionLessThanOrEqualTo
from sagemaker.workflow.condition_step import ConditionStep
from sagemaker.workflow.functions import JsonGet
from sagemaker.workflow.fail_step import FailStep
from sagemaker.workflow.functions import Join
from sagemaker.model_metrics import MetricsSource, ModelMetrics


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
    environment,  # dev,preprod or prod
    account_id,
    role=None,
    default_bucket=None,
    pipeline_name="AbalonePipeline",
    base_job_prefix="Abalone",
    project_name="SageMakerProjectName",
    model_package_group_name="Abalone",
    training_instance_type="ml.m5.xlarge",
):
    """Gets a SageMaker ML Pipeline instance working with on abalone data.

    Args:
        region: AWS region to create and run the pipeline.
        role: IAM role to create and run steps and pipeline.
        default_bucket: the bucket to use for storing the artifacts

    Returns:
        an instance of a pipeline
    """
    s3 = boto3.client("s3")
    print(f"Role: {role}")
    sagemaker_session = get_session(region, default_bucket)
    if role is None:
        role = sagemaker.session.get_execution_role(sagemaker_session)

    pipeline_session = get_pipeline_session(region, default_bucket)

    # get VPC parameters from Parameter store
    ssm = boto3.client("ssm")
    security_group_ids = ssm.get_parameter(Name="sagemaker-domain-sg")["Parameter"][
        "Value"
    ].split(",")
    subnets = ssm.get_parameter(Name="private-subnets-ids")["Parameter"]["Value"].split(
        ","
    )
    # parameters for pipeline execution
    processing_instance_count = ParameterInteger(
        name="ProcessingInstanceCount", default_value=1
    )
    processing_instance_type = ParameterString(
        name="ProcessingInstanceType", default_value="ml.m5.xlarge"
    )
    training_instance_count = ParameterInteger(
        name="TrainingInstanceCount", default_value=1
    )

    inference_instance_count = ParameterInteger(
        name="InferenceInstanceCount", default_value=1
    )
    inference_instance_type = ParameterString(
        name="InferenceInstanceType", default_value="ml.m5.xlarge"
    )

    input_data = ParameterString(
        name="InputDataUrl",
        default_value=f"s3://sagemaker-servicecatalog-seedcode-{region}"
        "/dataset/abalone-dataset.csv",
    )

    # Data for inference

    local_path = "abalone-dataset-batch"
    s3.download_file(
        f"sagemaker-servicecatalog-seedcode-{region}",
        "dataset/abalone-dataset-batch",
        local_path,
    )

    batch_data_uri = (
        f"s3://{default_bucket}/{base_job_prefix}/batch_inference/{local_path}"
    )
    s3.upload_file(
        local_path, default_bucket, f"{base_job_prefix}/batch_inference/{local_path}"
    )
    batch_data = ParameterString(
        name="BatchDataUrl",
        default_value=batch_data_uri,
    )
    mse_threshold = ParameterFloat(name="MseThreshold", default_value=8.0)

    # configure network for encryption, network isolation and VPC configuration
    network_config = NetworkConfig(
        enable_network_isolation=False,
        security_group_ids=security_group_ids,
        subnets=subnets,
        encrypt_inter_container_traffic=True,
    )

    # processing step for feature engineering

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
            ProcessingOutput(output_name="train", source="/opt/ml/processing/train"),
            ProcessingOutput(
                output_name="validation", source="/opt/ml/processing/validation"
            ),
            ProcessingOutput(output_name="test", source="/opt/ml/processing/test"),
        ],
        code=os.path.join(BASE_DIR, "preprocess.py"),
        arguments=["--input-data", input_data],
    )
    step_process = ProcessingStep(
        name="PreprocessData",
        step_args=step_args,
    )
    # training step for generating model artifacts
    model_path = f"s3://{sagemaker_session.default_bucket()}/{base_job_prefix}/Train"
    image_uri = sagemaker.image_uris.retrieve(
        framework="xgboost",
        region=region,
        version="1.0-1",
        py_version="py3",
        instance_type=training_instance_type,
    )
    xgb_train = Estimator(
        image_uri=image_uri,
        instance_type=training_instance_type,
        instance_count=training_instance_count,
        output_path=model_path,
        base_job_name=f"{base_job_prefix}/abalone-train",
        sagemaker_session=pipeline_session,
        subnets=network_config.subnets,
        security_group_ids=network_config.security_group_ids,
        encrypt_inter_container_traffic=True,
        enable_network_isolation=False,
        role=role,
    )
    xgb_train.set_hyperparameters(
        objective="reg:linear",
        num_round=50,
        max_depth=5,
        eta=0.2,
        gamma=4,
        min_child_weight=6,
        subsample=0.7,
        silent=0,
    )
    step_args = xgb_train.fit(
        inputs={
            "train": TrainingInput(
                s3_data=step_process.properties.ProcessingOutputConfig.Outputs[
                    "train"
                ].S3Output.S3Uri,
                content_type="text/csv",
            ),
            "validation": TrainingInput(
                s3_data=step_process.properties.ProcessingOutputConfig.Outputs[
                    "validation"
                ].S3Output.S3Uri,
                content_type="text/csv",
            ),
        },
    )
    step_train = TrainingStep(
        name="TrainModel",
        step_args=step_args,
    )

    # processing step for evaluation
    script_eval = ScriptProcessor(
        image_uri=image_uri,
        command=["python3"],
        instance_type=processing_instance_type,
        instance_count=1,
        base_job_name=f"{base_job_prefix}/script-abalone-eval",
        sagemaker_session=pipeline_session,
        network_config=network_config,
        role=role,
    )
    step_args = script_eval.run(
        inputs=[
            ProcessingInput(
                source=step_train.properties.ModelArtifacts.S3ModelArtifacts,
                destination="/opt/ml/processing/model",
            ),
            ProcessingInput(
                source=step_process.properties.ProcessingOutputConfig.Outputs[
                    "test"
                ].S3Output.S3Uri,
                destination="/opt/ml/processing/test",
            ),
        ],
        outputs=[
            ProcessingOutput(
                output_name="evaluation", source="/opt/ml/processing/evaluation"
            ),
        ],
        code=os.path.join(BASE_DIR, "evaluate.py"),
    )
    evaluation_report = PropertyFile(
        name="EvaluationReport",
        output_name="evaluation",
        path="evaluation.json",
    )
    step_eval = ProcessingStep(
        name="EvaluateModel",
        step_args=step_args,
        property_files=[evaluation_report],
    )

    # Create the model

    model = Model(
        image_uri=image_uri,
        model_data=step_train.properties.ModelArtifacts.S3ModelArtifacts,
        sagemaker_session=pipeline_session,
        role=role,
        vpc_config={"SecurityGroupIds": security_group_ids, "Subnets": subnets},
    )

    step_create_model = ModelStep(
        name=f"CreateModel",
        step_args=model.create(
            instance_type="ml.m5.large", accelerator_type="ml.eia1.medium"
        ),
    )

    # Batch inference
    transform_output_folder = "batch-output-abalone"
    output_path = "s3://{}/{}".format(
        default_bucket, f"{base_job_prefix}/{transform_output_folder}"
    )
    transformer = Transformer(
        model_name=step_create_model.properties.ModelName,
        instance_count=inference_instance_count,
        instance_type=inference_instance_type,
        sagemaker_session=PipelineSession(),
        output_path=output_path,
    )

    step_transform = TransformStep(
        name="Transform",
        step_args=transformer.transform(
            data=batch_data_uri,
            data_type="S3Prefix",
            job_name="Batch-{}-job".format(project_name),
        ),
    )

    model_metrics = ModelMetrics(
        model_statistics=MetricsSource(
            s3_uri="{}/evaluation.json".format(
                step_eval.arguments["ProcessingOutputConfig"]["Outputs"][0]["S3Output"][
                    "S3Uri"
                ]
            ),
            content_type="application/json",
        )
    )

    # Register the model

    register_args = model.register(
        content_types=["text/csv"],
        response_types=["text/csv"],
        inference_instances=["ml.t2.medium", "ml.m5.xlarge"],
        transform_instances=["ml.m5.xlarge"],
        model_package_group_name=model_package_group_name,
        approval_status="Approved",
        model_metrics=model_metrics,
    )
    step_register = ModelStep(name="RegisterModel", step_args=register_args)

    step_fail = FailStep(
        name="MSEFail",
        error_message=Join(
            on=" ", values=["Execution failed due to MSE >", mse_threshold]
        ),
    )

    # Condition to register and create inference o fail
    cond_lte = ConditionLessThanOrEqualTo(
        left=JsonGet(
            step_name=step_eval.name,
            property_file=evaluation_report,
            json_path="regression_metrics.mse.value",
        ),
        right=mse_threshold,
    )

    step_cond = ConditionStep(
        name="MSECond",
        conditions=[cond_lte],
        if_steps=[step_register, step_create_model, step_transform],
        else_steps=[step_fail],
    )

    # pipeline instance

    pipeline = Pipeline(
        name=pipeline_name,
        parameters=[
            processing_instance_count,
            inference_instance_count,
            training_instance_count,
            processing_instance_type,
            inference_instance_type,
            input_data,
            batch_data,
            mse_threshold,
        ],
        steps=[step_process, step_train, step_eval, step_cond],
        sagemaker_session=pipeline_session,
    )

    return pipeline
