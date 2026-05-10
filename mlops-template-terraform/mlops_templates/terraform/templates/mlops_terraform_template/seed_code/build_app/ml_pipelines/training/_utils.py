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

import logging

from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def resolve_ecr_uri_from_image_versions(sagemaker_session, image_versions, image_name):
    """Gets ECR URI from image versions
    Args:
        sagemaker_session: boto3 session for sagemaker client
        image_versions: list of the image versions
        image_name: Name of the image

    Returns:
        ECR URI of the image version
    """

    # Fetch image details to get the Base Image URI
    for image_version in image_versions:
        if image_version["ImageVersionStatus"] == "CREATED":
            image_arn = image_version["ImageVersionArn"]
            version = image_version["Version"]
            logger.info(f"Identified the latest image version: {image_arn}")
            response = sagemaker_session.sagemaker_client.describe_image_version(ImageName=image_name, Version=version)
            return response["ContainerImage"]
    return None


def resolve_ecr_uri(sagemaker_session, image_arn):
    """Gets the ECR URI from the image name

    Args:
        sagemaker_session: boto3 session for sagemaker client
        image_name: name of the image

    Returns:
        ECR URI of the latest image version
    """

    # Fetching image name from image_arn (^arn:aws(-[\w]+)*:sagemaker:.+:[0-9]{12}:image/[a-z0-9]([-.]?[a-z0-9])*$)
    image_name = image_arn.partition("image/")[2]
    try:
        # Fetch the image versions
        next_token = ""
        while True:
            response = sagemaker_session.sagemaker_client.list_image_versions(
                ImageName=image_name, MaxResults=100, SortBy="VERSION", SortOrder="DESCENDING", NextToken=next_token
            )

            ecr_uri = resolve_ecr_uri_from_image_versions(sagemaker_session, response["ImageVersions"], image_name)

            if ecr_uri is not None:
                return ecr_uri

            if "NextToken" in response:
                next_token = response["NextToken"]
            else:
                break

        # Return error if no versions of the image found
        error_message = f"No image version found for image name: {image_name}"
        logger.error(error_message)
        raise Exception(error_message)

    except (ClientError, sagemaker_session.sagemaker_client.exceptions.ResourceNotFound) as e:
        error_message = e.response["Error"]["Message"]
        logger.error(error_message)
        raise Exception(error_message)
