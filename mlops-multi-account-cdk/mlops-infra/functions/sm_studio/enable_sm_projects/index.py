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

# Function: EnableSagemakerProjects
# Purpose:  Enables Sagemaker Projects
import json
import boto3
import cfnresponse
from botocore.exceptions import ClientError

sm_client = boto3.client("sagemaker")
sc_client = boto3.client("servicecatalog")


def handler(event, context):
    try:
        if "RequestType" in event and event["RequestType"] in {"Create", "Update"}:

            properties = event["ResourceProperties"]
            roles = properties.get("ExecutionRoles", [])

            for role in roles:
                enable_sm_projects(role)

        cfnresponse.send(event, context, cfnresponse.SUCCESS, {}, "")
    except ClientError as exception:
        print(exception)
        cfnresponse.send(
            event,
            context,
            cfnresponse.FAILED,
            {},
            physicalResourceId=event.get("PhysicalResourceId"),
        )


def enable_sm_projects(studio_role_arn):
    # enable Project on account level (accepts portfolio share)
    response = sm_client.enable_sagemaker_servicecatalog_portfolio()

    print(response)

    # associate studio role with portfolio
    response = sc_client.list_accepted_portfolio_shares()

    print(response)

    portfolio_id = ""

    for portfolio in response["PortfolioDetails"]:
        if portfolio["ProviderName"] == "Amazon SageMaker":
            portfolio_id = portfolio["Id"]
            break

    response = sc_client.associate_principal_with_portfolio(
        PortfolioId=portfolio_id, PrincipalARN=studio_role_arn, PrincipalType="IAM"
    )

    print(response)
