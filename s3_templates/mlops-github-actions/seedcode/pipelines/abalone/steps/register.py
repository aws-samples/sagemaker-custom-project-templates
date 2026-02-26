"""Registration step: register model to SageMaker Model Registry.

Uses boto3 create_model_package to register the model, which triggers
the EventBridge rule for deployment workflow, after approval
"""
from sagemaker.mlops.workflow.function_step import step


def build_register_step(instance_type):
    """Return a @step-decorated model registration function."""

    @step(name="RegisterAbaloneModel", instance_type=instance_type)
    def register(
        model_package_group_name: str,
        model_s3_uri: str,
        image_uri: str,
        approval_status: str = "PendingManualApproval",
    ):
        import logging
        import boto3

        logger = logging.getLogger(__name__)

        sm_client = boto3.client("sagemaker")

        # Ensure the model package group exists
        try:
            sm_client.describe_model_package_group(
                ModelPackageGroupName=model_package_group_name
            )
        except sm_client.exceptions.ClientError:
            sm_client.create_model_package_group(
                ModelPackageGroupName=model_package_group_name,
                ModelPackageGroupDescription="Abalone model package group",
            )
            logger.info("Created model package group: %s", model_package_group_name)

        # Register model package
        response = sm_client.create_model_package(
            ModelPackageGroupName=model_package_group_name,
            InferenceSpecification={
                "Containers": [
                    {
                        "Image": image_uri,
                        "ModelDataUrl": model_s3_uri,
                    }
                ],
                "SupportedContentTypes": ["text/csv"],
                "SupportedResponseMIMETypes": ["text/csv"],
                "SupportedRealtimeInferenceInstanceTypes": [
                    "ml.t2.medium", "ml.m5.large"
                ],
                "SupportedTransformInstanceTypes": ["ml.m5.large"],
            },
            ModelApprovalStatus=approval_status,
        )
        logger.info(
            "Registered model package: %s",
            response["ModelPackageArn"],
        )

    return register