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


def get_approved_package(model_package_group_name):
    """Gets the latest approved model package for a model package group.
    Returns:
        The SageMaker Model Package ARN.
    """
    try:
        # Get the latest approved model package
        response = sm_client.list_model_packages(
            ModelPackageGroupName=model_package_group_name,
            ModelApprovalStatus="Approved",
            SortBy="CreationTime",
            MaxResults=100,
        )
        approved_packages = response["ModelPackageSummaryList"]
        # Fetch more packages if none returned with continuation token
        while len(approved_packages) == 0 and "NextToken" in response:
            logger.debug(f"Getting more packages for token: {response['NextToken']}")
            response = sm_client.list_model_packages(
                ModelPackageGroupName=model_package_group_name,
                ModelApprovalStatus="Approved",
                SortBy="CreationTime",
                MaxResults=100,
                NextToken=response["NextToken"],
            )
            approved_packages.extend(response["ModelPackageSummaryList"])
        # Return error if no packages found
        if len(approved_packages) == 0:
            error_message = f"No approved ModelPackage found for ModelPackageGroup: {model_package_group_name}"
            logger.error(error_message)
            raise Exception(error_message)
        # Return the pmodel package arn
        model_package_arn = approved_packages[0]["ModelPackageArn"]
        logger.info(f"Identified the latest approved model package: {model_package_arn}")
        return model_package_arn
    except ClientError as e:
        error_message = e.response["Error"]["Message"]
        logger.error(error_message)
        raise Exception(error_message) from e


# USED ONLY IF YOU CREATE MODEL_PACKAGE_GROUP(s) IN REPOSITORY AND NOT THROUGH SM PROJECT
def allow_cross_account_to_model_package(accounts, model_package_group_name):
    """Adds cross account acces to Model Package group and subsequent Model Packages
    Returns:
        A model package group policy
    """
    response = sm_client.describe_model_package_group(ModelPackageGroupName=model_package_group_name)
    model_package_group_arn = response["ModelPackageGroupArn"]

    if accounts["prod_account"]:
        model_package_group_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "1",
                    "Effect": "Allow",
                    "Principal": {"AWS":
                        [
                            f"arn:aws:iam::{accounts['preprod_account']}:root",
                            f"arn:aws:iam::{accounts['prod_account']}:root"
                        ]
                    },
                    "Action": ["sagemaker:DescribeModelPackageGroup"],
                    "Resource": model_package_group_arn,
                },
                {
                    "Sid": "2",
                    "Effect": "Allow",
                    "Principal": {"AWS":
                        [
                            f"arn:aws:iam::{accounts['preprod_account']}:root",
                            f"arn:aws:iam::{accounts['prod_account']}:root"
                        ]
                    },
                    "Action": [
                        "sagemaker:DescribeModelPackage",
                        "sagemaker:ListModelPackages",
                        "sagemaker:UpdateModelPackage",
                        "sagemaker:CreateModel",
                    ],
                    "Resource": f"{model_package_group_arn.replace('model-package-group','model-package')}/*",
                },
            ],
        }
    else:
        model_package_group_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "1",
                    "Effect": "Allow",
                    "Principal": {"AWS":
                        [
                            f"arn:aws:iam::{accounts['preprod_account']}:root"
                        ]
                    },
                    "Action": ["sagemaker:DescribeModelPackageGroup"],
                    "Resource": model_package_group_arn,
                },
                {
                    "Sid": "2",
                    "Effect": "Allow",
                    "Principal": {"AWS":
                        [
                            f"arn:aws:iam::{accounts['preprod_account']}:root"
                        ]
                    },
                    "Action": [
                        "sagemaker:DescribeModelPackage",
                        "sagemaker:ListModelPackages",
                        "sagemaker:UpdateModelPackage",
                        "sagemaker:CreateModel",
                    ],
                    "Resource": f"{model_package_group_arn.replace('model-package-group','model-package')}/*",
                },
            ],
        }
    
    return model_package_group_policy

        
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-package-group-name", type=str, required=True)
    # UNCOMMENT IF YOU CREATE MODEL_PACKAGE_GROUP(s) IN REPOSITORY AND NOT THROUGH SM PROJECT
    # parser.add_argument("--preprod-account", type=str, required=True)
    # parser.add_argument("--prod-account", type=str, default="")
    args = parser.parse_args()

    # Get the latest approved package
    model_package_arn = get_approved_package(args.model_package_group_name)
    
    # UNCOMMENT IF YOU CREATE MODEL_PACKAGE_GROUP(s) IN REPOSITORY AND NOT THROUGH SM PROJECT
    # accounts = {
    #     "preprod_account":args.preprod_account,
    #     "prod_account":args.prod_account
    # }
        
    # cross_account_policy = json.dumps(allow_cross_account_to_model_package(accounts, args.model_package_group_name))
    
    # # Set the new policy
    # sm_client.put_model_package_group_policy(
    #     ModelPackageGroupName=args.model_package_group_name, ResourcePolicy=cross_account_policy
    # )
    
    print(model_package_arn)
