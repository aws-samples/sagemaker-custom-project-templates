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
import requests
import cfnresponse
from botocore.exceptions import ClientError
import boto3
import json
import os
from base64 import b64encode
from nacl import encoding, public
from io import BytesIO
import zipfile
import base64


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


def encrypt_github_secret(public_key: str, secret_value: str) -> str:
    """Encrypt a Unicode string using the public key."""
    public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return b64encode(encrypted).decode("utf-8")


def access_github_public_key(gh_owner: str, gh_access_token: str, gh_repo: str) -> str:
    """Access GitHub public key"""
    headers = {
        "Authorization": f"Bearer {gh_access_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    public_key_url = f"https://api.github.com/repos/{gh_owner}/{gh_repo}/actions/secrets/public-key"
    response = requests.get(public_key_url, headers=headers)
    if response.status_code in [201, 200]:
        print(f"Successfully accessed the github public key")
    return response.json()['key_id'], response.json()['key']


def add_github_secret(gh_owner: str, gh_access_token: str, gh_repo: str, secret_name, secret_val):
    """Access GitHub public key"""
    # Access GitHub repo public key
    github_public_key_id, github_public_key = access_github_public_key(gh_owner, gh_access_token, gh_repo)
    headers = {
        "Authorization": f"Bearer {gh_access_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    secret_data = {
        "encrypted_value": encrypt_github_secret(github_public_key, secret_val),
        "key_id": github_public_key_id
    }
    gh_secret_url = f"https://api.github.com/repos/{gh_owner}/{gh_repo}/actions/secrets/{secret_name}"
    response = requests.put(gh_secret_url, headers=headers, json=secret_data)

    success_message = f"Successfully stored secret: {secret_name}"
    error_message = f"Error storing secret: {secret_name} ,  Error response got: {response.text}"
    check_gh_api_response(error_message, response, success_message)


# Check if the request was successful
def check_gh_api_response(error_message, response, success_message):
    if response.status_code < 400:
        print(success_message)
    else:
        print(error_message)
        raise Exception(error_message)


def set_build_secrets(properties):
    secrets = {
        "SAGEMAKER_PROJECT_NAME": properties.get("SAGEMAKER_PROJECT_NAME", ""),
        "SAGEMAKER_PROJECT_ID": properties.get("SAGEMAKER_PROJECT_ID", ""),
        "MODEL_PACKAGE_GROUP_NAME": properties.get("MODEL_PACKAGE_GROUP_NAME", ""),
        "AWS_REGION": properties.get("ACCOUNT_AWS_REGION", ""),
        "SAGEMAKER_PIPELINE_NAME": properties.get("SAGEMAKER_PIPELINE_NAME", ""),
        "SAGEMAKER_PIPELINE_DESCRIPTION": properties.get("SAGEMAKER_PIPELINE_DESCRIPTION", ""),
        "SAGEMAKER_PIPELINE_ROLE_ARN": properties.get("SAGEMAKER_PIPELINE_ROLE_ARN", ""),
        "ARTIFACT_BUCKET": properties.get("ARTIFACT_BUCKET", ""),
        "ARTIFACT_BUCKET_KMS_ID": properties.get("ARTIFACT_BUCKET_KMS_ID", ""),
        "PIPELINE_EXECUTION_IAM_ROLE": properties.get("PIPELINE_EXECUTION_IAM_ROLE", ""),

    }
    return secrets


def set_deploy_secrets(properties):
    secrets = {
        "SAGEMAKER_PROJECT_NAME": properties.get("SAGEMAKER_PROJECT_NAME", ""),
        "SAGEMAKER_PROJECT_ID": properties.get("SAGEMAKER_PROJECT_ID", ""),
        "MODEL_PACKAGE_GROUP_NAME": properties.get("MODEL_PACKAGE_GROUP_NAME", ""),
        "PIPELINE_EXECUTION_IAM_ROLE": properties.get("PIPELINE_EXECUTION_IAM_ROLE", ""),
        "AWS_REGION": properties.get("ACCOUNT_AWS_REGION", ""),
    }
    return secrets


def add_file_to_github(gh_owner: str, gh_access_token: str, gh_repo: str, content, file_path):
    """Checkin GitHub Content"""
    headers = {
        "Authorization": f"Bearer {gh_access_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    # Encode the env format values to base64 format
    content = base64.b64encode(content).decode('utf-8')
    payload = '{"message":"Sagemaker Project Code Initial CheckIn",' \
              '"committer":' \
              '{"name":"' + gh_owner + '",' \
                                       '"email":"octocat@github.com"},' \
                                       '"content": "' + content + '"}'

    content_url = f"https://api.github.com/repos/{gh_owner}/{gh_repo}/contents/{file_path}"

    # # Check if already file available on repo
    # content_response = requests.get(content_url, headers=headers)
    # if content_response.status_code in [200, 302]:
    #     print("File already available check Response:", content_response)
    #     payload += ',"sha": "' + content_response.json()['sha'] + '"}'
    # else:
    #     payload += '}'

    response = requests.put(content_url, headers=headers, data=payload)

    success_message = f"Successfully pushed file to github : {content_url}"
    error_message = f"Error pushing file to github : {content_url} ,  Error response got: {response.json()}"
    check_gh_api_response(error_message, response, success_message)
    return response


def create_github_repo(repo_name: str, repo_org: str, gh_access_token: str):
    repo_url = f"https://api.github.com/repos/{repo_org}/{repo_name}"

    create_repo_url = "https://api.github.com/user/repos"

    headers = {
        "Authorization": f"Bearer {gh_access_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    # Check if repo exists
    response = requests.get(repo_url, headers=headers)
    print("Response from repo get check: ", response)
    # If repo is doesn't exist then create the repo
    if response.status_code != 200:
        data = {
            "name": "{}".format(repo_name),
            "org": repo_org,
            "private": True,
            "visibility": "internal"
        }
        response = requests.post(create_repo_url, data=json.dumps(data), headers=headers)
        print("Response from repo create: ", response)
        success_message = f"Successfully created github repo : {repo_name}"
        error_message = f"Error in creating github repo : {repo_name} ,  Error response got: {response.json()}"
        check_gh_api_response(error_message, response, success_message)
    else:
        error_message = f"Skipping github repo creation, github repo with name : {repo_name} already exist."
        print(error_message)
        raise Exception(error_message)


def seed_code_to_repo(properties, repo_name, repo_org, PAT):
    # Push build and deploy seed code to github

    # Create an S3 client
    s3_client = boto3.client("s3")

    # Get the S3 bucket and key from the event data
    bucket_name = properties.get('S3_BUCKET_NAME')
    object_key = properties.get('S3_OBJECT_KEY')

    # Read the zip file from S3
    zip_data = s3_client.get_object(Bucket=bucket_name, Key=object_key)["Body"].read()

    # Create a BytesIO object from the zip data
    zip_bytes = BytesIO(zip_data)

    # Extract the files from the zip and write them to a temporary directory
    with zipfile.ZipFile(zip_bytes, "r") as zip_file:
        zip_file.extractall("/tmp/temp")
    github_workflow_files = dict()
    # Iterate over the files in the temporary directory
    for path, subdirs, files in os.walk("/tmp/temp"):
        for file in files:
            # Read the file data
            with open(os.path.join(path, file), "rb") as f:
                data = f.read()
            # Create new file in repo
            file_path = os.path.join(path, file).replace("/tmp/temp/", "")
            # to avoid trigger of GitHub workflow, while other files are not been seeded to GitHub repo
            if '.github/' in file_path:
                github_workflow_files[file_path] = data
            else:
                add_file_to_github(repo_org, PAT, repo_name, data, file_path)
    # seed the GitHub workflow files
    for file_path, data in github_workflow_files.items():
        add_file_to_github(repo_org, PAT, repo_name, data, file_path)


def handler(event, context):
    try:
        print(event)
        properties = event["ResourceProperties"]
        project_name = properties.get("SAGEMAKER_PROJECT_NAME", "")
        # Access secret from secret manager
        gh_owner, gh_access_token = get_github_secret(project_name)
        gh_repo = properties.get('GITHUB_REPO_NAME')

        # Create GitHub repository
        create_github_repo(repo_name=gh_repo, repo_org=gh_owner, gh_access_token=gh_access_token)

        # Set the secrets for both build and deploy repo
        secrets = {}
        if gh_repo and str(gh_repo).endswith('-build'):
            secrets = set_build_secrets(properties)
        elif gh_repo and str(gh_repo).endswith("-deploy"):
            secrets = set_deploy_secrets(properties)

        # Use GitHub API to create GitHub secrets
        for secret in secrets:
            add_github_secret(gh_owner, gh_access_token, gh_repo, secret, secrets[secret])

        # Push build and deploy seed code to GitHub
        seed_code_to_repo(properties, gh_repo, gh_owner, gh_access_token)

        if "RequestType" in event and event["RequestType"] in {"Create", "Update"}:
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {}, "")
        else:
            return {"statusCode": 200, "message": "Success"}
    except Exception as exception:
        print(exception)
        if "RequestType" in event and event["RequestType"] in {"Create", "Update"}:
            cfnresponse.send(
                    event,
                    context,
                    cfnresponse.FAILED,
                    {},
                    physicalResourceId=event.get("PhysicalResourceId"),
                )
        else:
            return {"statusCode": 500, "message": "Failure"}

