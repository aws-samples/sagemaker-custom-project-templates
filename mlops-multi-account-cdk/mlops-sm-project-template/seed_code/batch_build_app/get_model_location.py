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

import argparse
import json
import logging

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

"""Initialise boto3 SDK resources"""
sm_client = boto3.client("sagemaker")
s3_client = boto3.client("s3")

def get_model_location(model_package_arn):
    """Gets the S3 location for a model package.
    Returns:
        The SageMaker Model Package S3 URI.
    """
    
    model_package_description = sm_client.describe_model_package(ModelPackageName=model_package_arn)
    s3_uri = model_package_description["InferenceSpecification"]["Containers"][0]["ModelDataUrl"]
    logger.debug(f"Model S3 location: {s3_uri}")
    return s3_uri
    
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-package-arn", type=str, required=True)
    args = parser.parse_args()

    # Get the latest approved package
    model_s3_location = get_model_location(args.model_package_arn)
    
    print(model_s3_location)
    
    
    
    
