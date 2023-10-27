"""
    Lambda function used by SageMaker Project to 
    trigger CICD with GitHub Actions.
"""

import json
import logging
import os
import boto3
from botocore.exceptions import ClientError
from github import Github

logger = logging.getLogger()
logger.setLevel(logging.INFO)

git_access_token = os.environ["GITACCESSTOKEN"]
region = os.environ["REGION"]


def get_secret(secret_name):
    """Helper function to get secrets from AWS Secrets Manager"""
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region)
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name)
    except ClientError as get_secret_e:
        logger.error("Error: %s", get_secret_e)
    else:
        # Decrypts secret using the associated KMS key.
        if "SecretString" in get_secret_value_response:
            secret = get_secret_value_response["SecretString"]
    return json.loads(secret)


def lambda_handler(event, _):
    """Trigger GitHub workflow"""
    try:
        secret = get_secret(git_access_token)
        repo_name = event["ORG_REPO_NAME"]
        dict_inputs = {
            key.replace("INPUT_", ""): event[key]
            for key in event
            if key.startswith("INPUT_")
        }
        git = Github(secret["github_pat"])
        repo = git.get_repo(repo_name)
        for workflow in repo.get_workflows():
            # change branch for each case
            branch = repo.get_branch("main")
            workflow.create_dispatch(branch, inputs=dict_inputs)
            logger.info("Workflow has been triggered, repo: %s", repo.name)

    except ClientError as err:
        logger.error("Error: %s", err)
    return {"statusCode": "Done"}
