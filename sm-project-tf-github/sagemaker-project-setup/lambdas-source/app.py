# Lambda function to start the Seed Code CodeBuild project
# The CodeBuild project will copy the Seed Code to the Model GIT Repository

# Helper imports
import os

# Library Imports
import boto3

# Handler Function
def lambda_handler(event, context):

    try:
        print(event)
        client = boto3.client("codebuild")
        response = client.start_build(
            projectName=os.environ["CodeBuildProjectName"],
            environmentVariablesOverride=get_build_environment_variables_override(
                event
            ),
        )
        print(response)

    except Exception as error:
        print("Seed Code lambda_handler function error : {0}".format(error))


def get_build_environment_variables_override(event):

    try:
        env_variables = [
            {
                "name": "SEEDCODE_BUCKET_NAME",
                "value": event["SEEDCODE_BUCKET_NAME"],
                "type": "PLAINTEXT",
            },
            {
                "name": "SEEDCODE_BUCKET_KEY",
                "value": event["SEEDCODE_BUCKET_KEY"],
                "type": "PLAINTEXT",
            },
            {
                "name": "GIT_REPOSITORY_FULL_NAME",
                "value": event["GIT_REPOSITORY_FULL_NAME"],
                "type": "PLAINTEXT",
            },
            {
                "name": "GIT_REPOSITORY_BRANCH",
                "value": event["GIT_REPOSITORY_BRANCH"],
                "type": "PLAINTEXT",
            },
            {
                "name": "GIT_REPOSITORY_CONNECTION_ARN",
                "value": event["GIT_REPOSITORY_CONNECTION_ARN"],
                "type": "PLAINTEXT",
            },
        ]

        return env_variables

    except Exception as error:
        print("See Code Get Env Variables function error : {0}".format(error))
