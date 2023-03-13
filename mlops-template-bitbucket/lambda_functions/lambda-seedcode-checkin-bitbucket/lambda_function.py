import os
import boto3
import zipfile
import cfnresponse
import base64
from botocore.exceptions import ClientError
import logging
import uuid
import requests
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


def get_secret(secret):
    ''' '''
    secret_name = os.environ[secret]
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
            return decoded_binary_secret
            
    return None

def create_variable(base_url, workspace_name, repo_name, auth, key, value):

    response = requests.post(
        f'{base_url}/repositories/{workspace_name}/{repo_name}/pipelines_config/variables/', 
        auth=auth,
        json={
            'key': key, 
            'value': value,
            'secured': False
        }
    )
    return response


def lambda_handler(event, context):
    ''' '''
    response_data = {}
    if 'RequestType' in event:
        if not (event['RequestType'] == 'Create'):
            cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data)
            return

    sm_seed_code_bucket = os.environ['SeedCodeBucket']
    bitbucket_base_url = os.environ['BitbucketServer']
    model_build_sm_seed_code_object_name = os.environ['ModelBuildSeedCode'] 
    model_deploy_sm_seed_code_object_name = os.environ['ModelDeploySeedCode'] 
    region = os.environ['Region']
    workspace_name = os.environ['WorkspaceName']
    project_id = os.environ['SageMakerProjectId']
    project_name = os.environ['SageMakerProjectName']

    bitbucket_repo_name_build = os.environ['BuildProjectName'] + '-' + project_name
    bitbucket_repo_name_deploy = os.environ['DeployProjectName'] + '-' + project_name
    
    #Fetch IAM Access Key ID Secret
    FETCH_IAM_ACCESS_KEY_SECRET_ERROR_MSG = "IAM Access Key was not retrieved from Secrets Manager."
    try:
        iam_access_key = get_secret('IAMAccessKeySecretName') 
        if iam_access_key is None:
            raise Exception(FETCH_IAM_ACCESS_KEY_SECRET_ERROR_MSG)
        logging.info('Fetched IAM Access Key')
    except Exception as e:
        logging.error(FETCH_IAM_ACCESS_KEY_SECRET_ERROR_MSG)
        cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
        return {'message' : FETCH_IAM_ACCESS_KEY_SECRET_ERROR_MSG}

    #Fetch IAM Secret Key Secret
    FETCH_IAM_ACCESS_KEY_SECRET_ERROR_MSG = "IAM Secret Key was not retrieved from Secrets Manager."
    try:
        iam_secret_key = get_secret('IAMSecretKeySecretName') 
        if iam_secret_key is None:
            raise Exception(FETCH_IAM_ACCESS_KEY_SECRET_ERROR_MSG)
        logging.info('Fetched IAM Secret Key')
    except Exception as e:
        logging.error(FETCH_IAM_ACCESS_KEY_SECRET_ERROR_MSG)
        cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
        return {'message' : FETCH_IAM_ACCESS_KEY_SECRET_ERROR_MSG}
        
    # Fetch Bitbucket Username
    FETCH_BITBUCKET_USERNAME_SECRET_ERROR_MSG = "Bitbucket Username was not retrieved from Secrets Manager."
    try:
        bitbucket_username = get_secret('BitbucketUsernameSecretName')
        if bitbucket_username is None:
            raise Exception(FETCH_BITBUCKET_USERNAME_SECRET_ERROR_MSG)
        logging.info('Fetched username')
    except Exception as e:
        logging.error(FETCH_BITBUCKET_USERNAME_SECRET_ERROR_MSG)
        cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
        return {'message' : FETCH_BITBUCKET_USERNAME_SECRET_ERROR_MSG}
    
    # Fetch Bitbucket App Password
    FETCH_BITBUCKET_APP_PASSWORD_SECRET_ERROR_MSG = "Bitbucket App Password was not retrieved from Secrets Manager."
    try:
        bitbucket_password = get_secret('BitbucketAppPasswordSecretName')
        if bitbucket_password is None:
            raise Exception(FETCH_BITBUCKET_APP_PASSWORD_SECRET_ERROR_MSG)
        logging.info('Fetched password')
    except Exception as e:
        logging.error(FETCH_BITBUCKET_APP_PASSWORD_SECRET_ERROR_MSG)
        cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
        return {'message' : FETCH_BITBUCKET_APP_PASSWORD_SECRET_ERROR_MSG}
    
    # Create the Bitbucket Project
    logging.info(f"Project ID: {project_id.replace('-','_')}, Name: {os.environ['SageMakerProjectName']}")
    project_json_data = {"key": project_id.replace('-','_'), "name": os.environ['SageMakerProjectName']}
    try:
        response = requests.post(f'{bitbucket_base_url}/workspaces/{workspace_name}/projects', 
                                 json=project_json_data, 
                                 auth=(bitbucket_username, bitbucket_password))
        response_data = json.loads(response.content)
        if response.status_code//200 != 1:
            raise Exception(response_data)
        logging.info('Bitbucket Project created')
    except Exception as e:
        logging.error("The Project could not be created using the Bitbucket API..")
        logging.error(e)
        cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
        return {'message' : "Bitbucket project creation failed."}
    
    repo_json_data = {
        'scm': 'git',
        'is_private': True,
        'project': {
            'key': project_id.replace('-','_'),
        },
    }

    try:
        response = requests.post(f'{bitbucket_base_url}/repositories/{workspace_name}/{bitbucket_repo_name_build}', 
                                 json=repo_json_data,
                                 auth=(bitbucket_username, bitbucket_password))
        response_data = json.loads(response.content)
        if response.status_code//200 != 1:
            raise Exception(response_data)
        bitbucket_build_repo_url = response_data['links']['html']['href']
        logging.info(f'Bitbucket repository {bitbucket_repo_name_build} created')

    except Exception as e:
        logging.error("The Model Build Repository could not be created using the Bitbucket API..")
        logging.error(e)
        cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
        return {'message' : "Bitbucket repository creation failed."}


    try:
        response = requests.post(f'{bitbucket_base_url}/repositories/{workspace_name}/{bitbucket_repo_name_deploy}', 
                                 json=repo_json_data,
                                 auth=(bitbucket_username, bitbucket_password))
        response_data = json.loads(response.content)
        if response.status_code//200 != 1:
            raise Exception(response_data)
        bitbucket_deploy_repo_url = response_data['links']['html']['href']
        logging.info(f'Bitbucket repository {bitbucket_repo_name_deploy} created')
    except Exception as e:
        logging.error("The Model Deploy Repository could not be created using the Bitbucket API..")
        logging.error(e)
        cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
        return {'message' : "Bitbucket repository creation failed."}


    

    build_repo_variables = [
        {'key':'SAGEMAKER_PROJECT_NAME', 'value' : os.environ['SageMakerProjectName']},
        {'key':'SAGEMAKER_PROJECT_ID', 'value' : os.environ['SageMakerProjectId']},
        {'key':'AWS_REGION', 'value' : region},
        {'key':'ARTIFACT_BUCKET', 'value' : 'sagemaker-project-' + project_id},
        {'key':'SAGEMAKER_PROJECT_ARN', 'value':'arn:aws:sagemaker:' + region + ':' + os.environ['AccountId'] + ':project/' + os.environ['SageMakerProjectName']},
        {'key':'SAGEMAKER_PIPELINE_ROLE_ARN', 'value' : os.environ['Role']},
        {'key':'AWS_ACCESS_KEY_ID', 'value' : iam_access_key},
        {'key':'AWS_SECRET_ACCESS_KEY', 'value' : iam_secret_key}
    ]
    for variable in build_repo_variables:
        response = create_variable(bitbucket_base_url, 
                                  workspace_name, 
                                  bitbucket_repo_name_build, 
                                  (bitbucket_username, bitbucket_password), 
                                  variable['key'], variable['value'])
        response_data = json.loads(response.content)
        if response.status_code//200 != 1:
            logging.error("The variable(s) could not be created using the Bitbucket API..")
            logging.error(response.text)
            cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
            return {'message' : "Bitbucket repository variable creation failed."}
    logging.info(f'Bitbucket variables created for {bitbucket_repo_name_build}')
    
    deploy_repo_variables = [
        {'key':'SAGEMAKER_PROJECT_NAME', 'value' : os.environ['SageMakerProjectName']},
        {'key':'SAGEMAKER_PROJECT_ID', 'value' : os.environ['SageMakerProjectId']},
        {'key':'AWS_REGION', 'value' : region},
        {'key':'ARTIFACT_BUCKET', 'value' : 'sagemaker-project-' + os.environ['SageMakerProjectId']},
        {'key':'SAGEMAKER_PROJECT_ARN', 'value':'arn:aws:sagemaker:' + region + ':' + os.environ['AccountId'] + ':project/' + os.environ['SageMakerProjectName']},
        {'key':'MODEL_EXECUTION_ROLE_ARN', 'value' : os.environ['Role']},
        {'key':'AWS_ACCESS_KEY_ID', 'value' : iam_access_key},
        {'key':'AWS_SECRET_ACCESS_KEY', 'value' : iam_secret_key}
    ]
    for variable in deploy_repo_variables:
        response = create_variable(bitbucket_base_url, 
                                  workspace_name, 
                                  bitbucket_repo_name_deploy, 
                                  (bitbucket_username, bitbucket_password), 
                                  variable['key'], variable['value'])
        response_data = json.loads(response.content)
        if response.status_code//200 != 1:
            logging.error("The variable(s) could not be created using the Bitbucket API..")
            logging.error(response.text)
            cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
            return {'message' : "Bitbucket repository variable creation failed."}
    logging.info(f'Bitbucket variables created for {bitbucket_repo_name_deploy}')
    
    model_build_filename = f'/tmp/{str(uuid.uuid4())}-model-build-seed-code.zip'
    model_deploy_filename = f'/tmp/{str(uuid.uuid4())}-model-deploy-seed-code.zip'
    model_build_directory = f'/tmp/{str(uuid.uuid4())}-model-build'
    model_deploy_directory = f'/tmp/{str(uuid.uuid4())}-model-deploy'
    
    s3 = boto3.client('s3')
    # Get Model Build Seed Code from S3 for Gitlab Repo
    with open(model_build_filename, 'wb') as f:
        s3.download_fileobj(sm_seed_code_bucket, model_build_sm_seed_code_object_name, f)
        logging.info(f'S3 Download complete for {model_build_filename}')
        
    # Get Model Deploy Seed Code from S3 for Gitlab Repo
    with open(model_deploy_filename, 'wb') as f:
        s3.download_fileobj(sm_seed_code_bucket, model_deploy_sm_seed_code_object_name, f)
        logging.info(f'S3 Download complete for {model_deploy_filename}')
        
    # Extract Zip file of seed code to local dir
    try:
        with zipfile.ZipFile(model_build_filename) as z:
            z.extractall(model_build_directory)
            logging.info(f"Extracted all for {model_build_filename}")
    except:
        response_data = {"message": f"Invalid file {model_build_filename}"}
        cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
        logging.error(response_data['message'])
        return response_data
    
    try:
        with zipfile.ZipFile(model_deploy_filename) as z:
            z.extractall(model_deploy_directory)
            logging.info(f"Extracted all for {model_deploy_filename}")
    except:
        response_data = {"message": f"Invalid file {model_deploy_filename}"}
        cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
        logging.error(response_data['message'])
        return response_data

    data = []
    for dir_path in (model_build_directory, model_deploy_directory):
        logging.info(f"Reading files from {dir_path}")
        data_files = {}
        for path, _, files in os.walk(dir_path): 
            for name in files:
                full_file_path = os.path.join(path, name)
                if name.endswith('.DS_Store'):
                    continue
                if name.startswith('._'):
                    continue
                else:
                    dir = dir_path + "/"
                    try:
                        logging.info(f"Reading file at path: {full_file_path}")
                        data_files[full_file_path.split(dir)[1]] = open(full_file_path, 'rb').read()
                    except:
                        pass
        data.append(data_files)
    
    response_data = {}
    build_data, deploy_data = data[0], data[1]
    try:
        response = requests.post(f'{bitbucket_base_url}/repositories/{workspace_name}/{bitbucket_repo_name_build}/src', 
                                 files=build_data, 
                                 auth=(bitbucket_username, bitbucket_password))
        
        if response.status_code//200 != 1:
            response_data = json.loads(response.content)
            raise Exception(response_data)
        logging.info(f'Bitbucket commit successful for {bitbucket_repo_name_build}')
    except Exception as e:
        logging.error("Code could not be pushed to the model build repo.")
        logging.error(e)
        cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
        return { 
            'message' : "Bitbucket seedcode checkin failed."
        }
    response_data = {}
    try:
        response = requests.post(f'{bitbucket_base_url}/repositories/{workspace_name}/{bitbucket_repo_name_deploy}/src', 
                                 files=deploy_data, 
                                 auth=(bitbucket_username, bitbucket_password))
        if response.status_code//200 != 1:
            response_data = json.loads(response.content)
            raise Exception(response_data)
        logging.info(f'Bitbucket commit successful for {bitbucket_repo_name_deploy}')
    except Exception as e:
        logging.error("Code could not be pushed to the model deploy repo.")
        logging.error(e)
        cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
        return { 
            'message' : "Bitbucket seedcode checkin failed."
        }
    
    response_data = { 
        'message' : "Bitbucket seedcode checkin successfully completed",
        'build_repo_url': bitbucket_build_repo_url,
        'deploy_repo_url': bitbucket_deploy_repo_url
    }
    logger.info("Successfully checked in seed code to Bitbucket..")
    cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data)
    
    return response_data
