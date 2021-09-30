import gitlab
import os
import boto3
import base64
from botocore.exceptions import ClientError

def get_secret():
    ''' '''
    secret_name = os.environ['SecretName']
    region_name = os.environ['Region']
    
    print("Region: ", region_name)
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
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            secret_arn = get_secret_value_response['ARN']
        else:
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
            secret_arn = get_secret_value_response['ARN']
            return decoded_binary_secret.split(':')[-1].strip('"}'), secret_arn

    return secret.split(':')[-1].strip('"}'), secret_arn

def lambda_handler(event, context):
    ''' '''
    gitlab_project_name = os.environ['DeployProjectName']
    gitlab_private_token = get_secret() #DO NOT HARDCODE THIS - PULL FROM SECRETS MANAGER/SECURE VAULT
 
    #Configure SDKs for GitLab and S3
    gl = gitlab.Gitlab('https://gitlab.com', private_token=gitlab_private_token)
 
    try:
        #Create the GitLab Project
        project = gl.projects.list(search = gitlab_project_name)[0]
        trigger = project.triggers.create({'description' : gitlab_project_name + '-lambda-generated-token'})
        token = trigger.token
        project.trigger_pipeline('main', token)
        trigger.delete()
    except:
        print("Failed to trigger pipeline..")
