import json
import logging
import os
import requests
import json

import boto3
from botocore.exceptions import ClientError
from github import Github, UnknownObjectException

import cfnresponse

logger = logging.getLogger()
logger.setLevel(logging.INFO)

region = os.environ["REGION"]
git_access_token = os.environ["GITACCESSTOKEN"]


def get_secret(secret_name):
    """Helper function to get secret from AWS Sectets Manager"""
    client = boto3.client(service_name="secretsmanager", region_name=region)
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as get_secret_e:
        logger.error("Error: %s", get_secret_e)
    else:
        # Decrypts secret using the associated KMS key.
        if "SecretString" in get_secret_value_response:
            secret = get_secret_value_response["SecretString"]
    return json.loads(secret)


def does_repo_exist(github_client, repo_name):
    """Check if GitHub repo exists"""
    try:
        github_client.get_repo(repo_name)
        return True
    except UnknownObjectException:
        logger.info("Repo %s does not exist", repo_name)
        return False


def create_secret_git(git, organization, repo_name, dict_secrets):
    """Create secrets in GitHub repo"""
    organization = git.get_organization(organization)
    new_repo = organization.get_repo(repo_name)
    for key in dict_secrets:
        new_repo.create_secret(key, dict_secrets.get(key))
        logger.info("Secret %s added", key)


def add_admin_collaborator(git, organization, repo_name, git_user):
    """Add admin users to github repo"""
    organization = git.get_organization(organization)
    repo = organization.get_repo(repo_name)
    repo.add_to_collaborators(git_user, "admin")


def create_production_environment(git, organization, repo_name, git_user, pat, env_name="production"):
    """Add environment called `production` for GitHub actions."""
    # Get integer id for usernace
    users = git.search_users(f"{git_user} in:login")
    usr_id = users.get_page(0)[0].id
    data = {"reviewers": [{"type": "User", "id": usr_id}]}

    # Create header and data for GutHub API call
    # https://docs.github.com/en/rest/deployments/environments#create-or-update-an-environment
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {pat}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    response = requests.put(
        f"https://api.github.com/repos/{organization}/{repo_name}/environments/{env_name}",
        headers=headers,
        data=json.dumps(data),
    )
    logger.info("Add environment response: %s", json.dumps(response.json()))
    return response


# Clone repo from a template
def clone_template_repo(git, organization, template_repo, repo_name, pat):
    """Create a repository from a template"""
    # Create header and data for GutHub API call
    # https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#create-a-repository-using-a-template
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {pat}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    if does_repo_exist(git, f"{organization}/{template_repo}") and not does_repo_exist(
        git, f"{organization}/{repo_name}"
    ):
        try:
            data = {
                "owner": organization,
                "name": repo_name,
                "description": f"Repository created from {template_repo}",
                "include_all_branches": True,
                "private": True,
            }

            response_repo = requests.post(
                f"https://api.github.com/repos/{organization}/{template_repo}/generate",
                headers=headers,
                data=json.dumps(data),
            )
            print(response_repo.json())
            logger.info("Response: %s", response_repo)
            returncode = 200
        except Exception as clone_template_error:
            logger.error("Error: %s", clone_template_error)
    else:
        logger.info("Template does not exists")
        returncode = 405
    return returncode


def add_repo_variable(organization, repo_name, pat, dict_var):
    """Add repository variables to github repo"""
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {pat}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = dict_var

    response = requests.post(
        f"https://api.github.com/repos/{organization}/{repo_name}/actions/variables",
        headers=headers,
        data=json.dumps(data),
    )
    logger.info("Add repository variable response: %s", json.dumps(response.json()))
    return response


# Main function
def lambda_handler(event, context):
    """Clone a private GitHub repo from a template repo"""
    # Get personal access token to make GitHub API calls
    secret = get_secret(git_access_token)
    # Get cloudformation properties
    repo_name = event["ResourceProperties"]["REPO_NAME"]
    template_repo = event["ResourceProperties"]["TEMPLATE_REPO"]
    organization = event["ResourceProperties"]["ORGANIZATION"]
    git_user = event["ResourceProperties"]["GIT_USER"]
    dict_secrets = {
        key.replace("SECRET_", ""): event["ResourceProperties"][key]
        for key in event["ResourceProperties"]
        if key.startswith("SECRET_")
    }
    try:
        git = Github(secret["github_pat"])
        # Create repo from tenplate
        returncode = clone_template_repo(
            git, organization, template_repo, repo_name, secret["github_pat"]
        )
        # Add provided list of usernames as Admin
        add_admin_collaborator(git, organization, repo_name, git_user)
        # Add all GitHub Secrets
        if dict_secrets:
            create_secret_git(git, organization, repo_name, dict_secrets)
        # Add all Github repository variables
        for key in event["ResourceProperties"]:
            if key.startswith("VAR_"):
                dict_var = {}
                dict_var.update({"name": key.replace("VAR_", "")})
                dict_var.update({"value": event["ResourceProperties"][key]})
                add_repo_variable(
                    organization, repo_name, secret["github_pat"], dict_var
                )

        # Create a deployment environment requiring manual approaval from
        #  provided username.
        create_production_environment(git, organization,repo_name, git_user, secret["github_pat"])
        cfnresponse.send(
            event, context, cfnresponse.SUCCESS, {}, context.log_stream_name
        )
    except Exception as err:
        logger.error("Error:%s", err)
        cfnresponse.send(
            event, context, cfnresponse.FAILED, {}, context.log_stream_name
        )
    return {"statusCode": returncode}
