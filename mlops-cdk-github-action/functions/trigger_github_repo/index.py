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

# Function: SeedGithubRepo
# Purpose: Seed GitHub Repo
from datetime import datetime

import requests
from botocore.exceptions import ClientError
import boto3
import json
import os


def get_github_secret(project_name):
    # Create a Secrets Manager client
    secrets_manager_client = boto3.client("secretsmanager")

    # Get the secret from Secrets Manager
    secret_value = secrets_manager_client.get_secret_value(
        SecretId=f"GithubSecret-{project_name}"
    )["SecretString"]

    # Parse the secret value as JSON
    secret_data = json.loads(secret_value)
    # Use the secret data
    owner = secret_data["owner"]
    access_key = secret_data["access_key"]
    return owner, access_key


def start_github_workflow(gh_owner: str, gh_access_token: str, gh_repo: str):
    headers = {
        "Authorization": f"Bearer {gh_access_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    # check the details of the GitHub Action API :
    # https://docs.github.com/en/rest/actions/workflows?apiVersion=2022-11-28#create-a-workflow-dispatch-event
    workflow_id = 'deploy_model_pipeline.yml'
    content_url = f"https://api.github.com/repos/{gh_owner}/{gh_repo}/actions/workflows/{workflow_id}/dispatches"
    content_response = requests.post(content_url, headers=headers, data='{"ref":"main"}')
    return content_response


def handler(event, context):
    try:
        project_name = os.environ['SAGEMAKER_PROJECT_NAME']
        # Access github secret from aws secret manager
        gh_owner, gh_access_token = get_github_secret(project_name)
        gh_repo = os.environ['GITHUB_REPO_NAME']

        # Listen the Model Approval events from AWS Event Bridge
        if "source" in event and event["source"] in {"aws.sagemaker"}:
            response = start_github_workflow(gh_owner, gh_access_token, gh_repo)
            # Check if the request was successful
            if response.status_code in [201, 200, 204]:
                print(f"Successfully model approval event triggered github action deploy pipeline")
            else:
                print(response)
                print(f"Failed to trigger github action deploy pipeline on Github repo : {gh_repo}")

    except ClientError as exception:
        print(f"Failed to trigger github action deploy pipeline on Github repo : {gh_repo}")
        print(exception)