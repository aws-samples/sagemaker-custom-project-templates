import os
import base64
import logging
import boto3
from botocore.exceptions import ClientError
from github import Github

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


def get_secret():
    secret_name = os.environ["GitHubTokenSecretName"]
    region_name = os.environ["Region"]

    session = boto3.session.Session()
    client = session.client(
        service_name="secretsmanager", region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "DecryptionFailureException":
            logging.error(e)
            raise e
        elif e.response["Error"]["Code"] == "InternalServiceErrorException":
            logging.error(e)
            raise e
        elif e.response["Error"]["Code"] == "InvalidParameterException":
            logging.error(e)
            raise e
        elif e.response["Error"]["Code"] == "InvalidRequestException":
            logging.error(e)
            raise e
        elif e.response["Error"]["Code"] == "ResourceNotFoundException":
            logging.error(e)
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Get the value whether the secret is a string or binary.
        if "SecretString" in get_secret_value_response:
            secret = get_secret_value_response["SecretString"]
            return secret.split(":")[-1].strip('" "}\n')
        else:
            decoded_binary_secret = base64.b64decode(
                get_secret_value_response["SecretBinary"]
            )
            return decoded_binary_secret.split(":")[-1].strip('"}')

    return None


def lambda_handler(event, context):
    github_repo_name = os.environ["DeployRepoName"]
    github_workflow_name = os.environ["GitHubWorkflowNameForDeployment"]
    github_token = get_secret()

    if github_token is None:
        raise Exception("Failed to retrieve secret from Secrets Manager")

    # Connecting to GitHub using Token Access
    g = Github(github_token)

    # Getting repository and trigger the deploy GitHub workflow
    try:
        repo = g.get_user().get_repo(github_repo_name)
        workflow = repo.get_workflow(github_workflow_name)
        branch = repo.get_branch("main")
        res = workflow.create_dispatch(branch)

        # If res is False, it has failed.
        if not res:
            raise Exception()

    except Exception:
        message = "Failed to trigger the GitHub workflow"
        logger.error(message, exc_info=1)
        return {"message": message}

    return {"message": "Success!"}