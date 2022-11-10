# Lambda function to add the Seed Code to the Gitlab Repository

# Helper Imports
import os
import logging
import time
import base64

# Library Imports
import gitlab
import boto3
from botocore.exceptions import ClientError

# Logger Set up
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


def lambda_handler(event, context):

    gitlab_server_uri = os.environ["GitLabServer"]
    region = os.environ["Region"]
    gitlab_project_name_build = os.environ["BuildProjectName"]
    gitlab_repo_branch = os.environ["GitlabBranch"]

    # Fetch GitLab Token Secret

    FETCH_GITLAB_TOKEN_SECRET_ERROR_MSG = (
        "GitLab token was not retrieved from Secrets Manager."
    )

    try:
        gitlab_private_token = get_secret("GitLabTokenSecretName")
        if gitlab_private_token is None:
            raise Exception(FETCH_GITLAB_TOKEN_SECRET_ERROR_MSG)

    except Exception as e:
        logging.error(FETCH_GITLAB_TOKEN_SECRET_ERROR_MSG)
        # cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
        return {"message": FETCH_GITLAB_TOKEN_SECRET_ERROR_MSG}

    # Fetch IAM Access Key ID Secret

    FETCH_IAM_ACCESS_KEY_SECRET_ERROR_MSG = (
        "IAM Access Key was not retrieved from Secrets Manager."
    )

    try:
        iam_access_key = get_secret("IAMAccessKeySecretName")
        if iam_access_key is None:
            raise Exception(FETCH_IAM_ACCESS_KEY_SECRET_ERROR_MSG)

    except Exception as e:
        logging.error(FETCH_IAM_ACCESS_KEY_SECRET_ERROR_MSG)
        # cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
        return {"message": FETCH_IAM_ACCESS_KEY_SECRET_ERROR_MSG}

    # Fetch IAM Secret Key Secret

    FETCH_IAM_ACCESS_KEY_SECRET_ERROR_MSG = (
        "IAM Secret Key was not retrieved from Secrets Manager."
    )

    try:
        iam_secret_key = get_secret("IAMSecretKeySecretName")
        if iam_secret_key is None:
            raise Exception(FETCH_IAM_ACCESS_KEY_SECRET_ERROR_MSG)

    except Exception as e:
        logging.error(FETCH_IAM_ACCESS_KEY_SECRET_ERROR_MSG)
        # cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
        return {"message": FETCH_IAM_ACCESS_KEY_SECRET_ERROR_MSG}

    # Configure SDKs for GitLab

    gl = gitlab.Gitlab(gitlab_server_uri, private_token=gitlab_private_token)

    # Create the GitLab Project

    try:

        # Check if the Gitlab Project exists
        project_list_resp = gl.projects.list(search=gitlab_project_name_build)
        project_list = []

        for build_project in project_list_resp:
            build_proj_name = build_project.name
            proj_name_with_ns = build_project.name_with_namespace

            project_list.append(build_proj_name)
            if build_proj_name == gitlab_project_name_build:
                build_proj_id = build_project.id

        if gitlab_project_name_build in project_list:
            print("Gitlab project already existing")
            # Delete the Gitlab Project if exists

            project_delete_resp = gl.projects.delete(build_proj_id)
            print("Deleting the Gitlab Project ... ")

            time.sleep(60)
            print("Creating Gitlab project ...")
            build_project = gl.projects.create({"name": gitlab_project_name_build})
        else:
            print("Gitlab project not found. Creating ....")

            build_project = gl.projects.create({"name": gitlab_project_name_build})

    except Exception as e:
        logging.error("The Project could not be created using the GitLab API..")
        logging.error(e)
        # cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
        return {"message": "GitLab seedcode checkin failed."}

    # Create project variables in model build and deploy repos
    try:
        build_project.variables.create(
            {
                "key": "SAGEMAKER_PROJECT_NAME",
                "value": os.environ["SageMakerProjectName"],
            }
        )
        build_project.variables.create(
            {"key": "SAGEMAKER_PROJECT_ID", "value": os.environ["SageMakerProjectId"]}
        )
        build_project.variables.create({"key": "AWS_REGION", "value": region})
        build_project.variables.create(
            {
                "key": "ARTIFACT_BUCKET",
                "value": "sagemaker-project-" + os.environ["SageMakerProjectId"],
            }
        )
        build_project.variables.create(
            {
                "key": "SAGEMAKER_PROJECT_ARN",
                "value": "arn:aws:sagemaker:"
                + region
                + ":"
                + os.environ["AccountId"]
                + ":project/"
                + os.environ["SageMakerProjectName"],
            }
        )
        build_project.variables.create(
            {
                "key": "SAGEMAKER_PIPELINE_ROLE_ARN",
                "value": os.environ["SageMakerPipelineRoleArn"],
            }
        )
        build_project.variables.create(
            {"key": "AWS_ACCESS_KEY_ID", "value": iam_access_key}
        )
        build_project.variables.create(
            {"key": "AWS_SECRET_ACCESS_KEY", "value": iam_secret_key}
        )

    except Exception as e:
        logging.error("Project variables could not be created for model build")
        logging.error(e)
        # cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
        return {"message": "GitLab seedcode checkin failed."}

    model_build_directory = f"seedcode/mlops-gitlab-project-seedcode-model-build"

    # Iterate through all of the files in the extracted folder to create commmit data

    build_data = {
        "branch": gitlab_repo_branch,
        "commit_message": "Initial Commit",
        "actions": [],
    }

    for path, _, files in os.walk(model_build_directory):
        for name in files:
            full_file_path = os.path.join(path, name)
            if name.endswith(".DS_Store"):
                continue
            if name.startswith("._"):
                continue
            else:
                dir = model_build_directory + "/"
                try:
                    build_action = {
                        "action": "create",
                        "file_path": full_file_path.split(dir)[1],
                        "content": open(full_file_path).read(),
                    }
                    build_data["actions"].append(build_action)
                except:
                    pass

    # Commit to the above created Repo all the files that were in the seed code Zip

    try:
        build_project.commits.create(build_data)
    except Exception as e:
        logging.error("Code could not be pushed to the model build repo.")
        logging.error(e)
        # cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
        return {"message": "GitLab seedcode checkin failed."}

    logger.info("Successfully checked in seed code to GitLab..")

    return {"message": "GitLab seedcode checkin successfully completed"}


def get_secret(secret):

    secret_name = os.environ[secret]
    region_name = os.environ["Region"]

    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
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
            logging.error(e)
            raise e
    else:
        if "SecretString" in get_secret_value_response:
            secret = get_secret_value_response["SecretString"]
            return secret.split(":")[-1].strip('" "}\n')
        else:
            decoded_binary_secret = base64.b64decode(
                get_secret_value_response["SecretBinary"]
            )
            return decoded_binary_secret

    return None
