import logging
from typing import Union
import time

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def get_s3_bucket_and_key(s3_uri: str) -> str:
    """Function to return bucket name and key for a given s3 uri.
    Args: s3_uri: s3 uri such as s3://bucket/file.txt or s3://bucket/prefix
    Returns: bucket_name, key
    """
    uri_parts = s3_uri.replace("s3://", "").split("/")
    return uri_parts[0], "/".join(uri_parts[1:])


def download_file_from_s3(s3_uri: str, local_path: str, s3_client=None) -> None:
    """Function to download file from s3
    Args:
        s3_uri: s3 location of file such as s3://bucket/file.txt
        local_path: local path to store the file
        s3_client: boto3.client("s3"). If not provided, one is created with default credentials.
    Returns:
    """
    if not s3_client:
        s3_client = boto3.client("s3")
    bucket, key = get_s3_bucket_and_key(s3_uri)
    s3_client.download_file(bucket, key, local_path)


def upload_file_to_s3(local_path: str, s3_uri: str, s3_client=None) -> None:
    """Function to upload file to s3
    Args:
        local_path: local path of file.
        s3_uri: s3 location of file such as s3://bucket/file.txt
        s3_client: boto3.client("s3"). If not provided, one is created with default credentials.
    Returns:
    """
    if not s3_client:
        s3_client = boto3.client("s3")
    bucket, key = get_s3_bucket_and_key(s3_uri)
    s3_client.upload_file(local_path, bucket, key)


def check_if_model_package_exists(
    model_package_name: str, sm_client=None
) -> Union[str, None]:
    """Function to check if a SageMaker Model Package exists
    Args:
        model_package_name: Name of SageMaker model package
        sm_client: boto3.client("sagemaker"). If not provided,
            one is created with default credentials.
    Returns:
        model_package_arn: str. `None` if no model package was found.
    """
    if not sm_client:
        sm_client = boto3.client("sagemaker")
    try:
        return sm_client.describe_model_package(ModelPackageName=model_package_name)[
            "ModelPackageName"
        ]
    except ClientError as err:
        logger.info("Model Package %s not found.", model_package_name)
        logger.info("%s", err)
        return None


def get_cfn_style_config(stage_parameters: dict) -> list:
    """Change formatting of config for CloudFormation"""
    parameters = []
    for key, value in stage_parameters.items():
        param = f"{key}={value}"
        parameters.append(param)
    return parameters


def waits_model_package_complete(model_package_name: str, sm_client=None) -> None:
    """Function to check if a SageMaker Model Package is in Completed status
    Args:
        model_package_name: Name of SageMaker model package
        sm_client: boto3.client("sagemaker"). If not provided,
            one is created with default credentials.
    Returns:
        `None`
    """
    if not sm_client:
        sm_client = boto3.client("sagemaker")
    status = None
    try:
        while status != ("Completed" or "Failed" or "Deleting"):
            status = sm_client.describe_model_package(
                ModelPackageName=model_package_name
            )["ModelPackageStatus"]
            time.sleep(5)
        if status == "Failed":
            raise Exception("ModelPackage found status {status}")
    except ClientError as err:
        logger.info("Model Package %s not found.", model_package_name)
        logger.info("%s", err)
