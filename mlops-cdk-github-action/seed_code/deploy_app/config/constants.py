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

import boto3
import os
from dotenv import load_dotenv

load_dotenv()  # take environment variables from GitHub Action

DEFAULT_DEPLOYMENT_REGION = os.getenv("AWS_REGION", "us-east-1")

ssm_client = boto3.client("ssm", region_name=DEFAULT_DEPLOYMENT_REGION)

DEV_ACCOUNT = ssm_client.get_parameter(Name="/mlops/dev/account_id")["Parameter"]["Value"]

PROJECT_NAME = os.getenv("SAGEMAKER_PROJECT_NAME", "")
PROJECT_ID = os.getenv("SAGEMAKER_PROJECT_ID", "")
MODEL_PACKAGE_GROUP_NAME = os.getenv("MODEL_PACKAGE_GROUP_NAME", "")
MODEL_BUCKET_ARN = os.getenv("MODEL_BUCKET_ARN", "arn:aws:s3:::*mlops*")
ECR_REPO_ARN = os.getenv("ECR_REPO_ARN", None)
