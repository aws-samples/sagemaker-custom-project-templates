import gitlab
import os
import boto3
import base64
from botocore.exceptions import ClientError

def get_secret():
    ''' '''
    secret_name = os.environ['SecretName']
    region_name = os.environ['Region']
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    get_secret_value_response = client.get_secret_value(
        SecretId=secret_name
    )
    secret = get_secret_value_response['SecretString']
    return secret.split(':')[-1].strip('"}')

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
