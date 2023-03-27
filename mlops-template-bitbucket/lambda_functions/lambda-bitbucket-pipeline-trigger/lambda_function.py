import requests
import os
import json
import boto3
import base64
from botocore.exceptions import ClientError

import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

def get_secret(secret_name):
    ''' '''
    secret_name = os.environ[secret_name]
    region_name = os.environ['Region']

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            logging.error(e)
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            logging.error(e)
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            logging.error(e)
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            logging.error(e)
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            logging.error(e)
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            
            return secret.split(':')[-1].strip('" "}\n')
        else:
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
            return decoded_binary_secret.split(':')[-1].strip('"}')

    return None

def lambda_handler(event, context):
    ''' '''
    bitbucket_repo_name = os.environ['DeployProjectName']
    bitbucket_server_uri = os.environ['BitbucketServer']
    bitbucket_username = get_secret('BitbucketUsernameSecretName')
    bitbucket_password = get_secret('BitbucketAppPasswordSecretName')
    workspace_name = os.environ['WorkspaceName']

    try:
        if bitbucket_username is None or bitbucket_password is None:
            raise Exception("Failed to retrieve secret from Secrets Manager")
    
        response = requests.post(
            f'{bitbucket_server_uri}/repositories/{workspace_name}/{bitbucket_repo_name}/pipelines/',
            auth=(bitbucket_username, bitbucket_password),
            json = {
                "target": {
                    "ref_type": "branch",
                    "type": "pipeline_ref_target",
                    "ref_name": "master"
                }
            }
        )
        if response.status_code//200 != 1:
            raise Exception(json.loads(response.content))
    except Exception as e:
        logging.error("Failed to trigger pipeline..")
        logging.error(e)
        return {
            'message' : "Failed to trigger pipeline.."
        }

    return {
            'message' : "Success!"
        }
