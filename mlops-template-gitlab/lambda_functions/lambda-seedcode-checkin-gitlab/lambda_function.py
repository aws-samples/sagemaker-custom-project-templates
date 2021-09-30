import gitlab
import os
import boto3
import zipfile
import cfnresponse
import base64
from botocore.exceptions import ClientError
import logging
import uuid

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

def get_secret():
    ''' '''
    secret_name = os.environ['SecretName']
    region_name = os.environ['Region']
    
    logging.info("Region: ", region_name)
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

    return secret.split(':')[-1].strip('"}'), secret_arn

def lambda_handler(event, context):
    ''' '''
    sm_seed_code_bucket = os.environ['SeedCodeBucket']
    model_build_sm_seed_code_object_name = os.environ['ModelBuildSeedCode'] 
    model_deploy_sm_seed_code_object_name = os.environ['ModelDeploySeedCode'] 
    region = os.environ['Region']
    
    gitlab_project_name_build = os.environ['BuildProjectName'] + '-' + os.environ['SageMakerProjectId']
    gitlab_project_name_deploy = os.environ['DeployProjectName'] + '-' + os.environ['SageMakerProjectId']
    gitlab_private_token, secret_arn = get_secret() 
 
    #Configure SDKs for GitLab and S3
    gl = gitlab.Gitlab('https://gitlab.com', private_token=gitlab_private_token)
    s3 = boto3.client('s3')
 
    model_build_filename = f'/tmp/{str(uuid.uuid4())}-model-build-seed-code.zip'
    model_deploy_filename = f'/tmp/{str(uuid.uuid4())}-model-deploy-seed-code.zip'
    model_build_directory = f'/tmp/{str(uuid.uuid4())}-model-build'
    model_deploy_directory = f'/tmp/{str(uuid.uuid4())}-model-deploy'

    # #Get Model Build Seed Code from S3 for Gitlab Repo
    with open(model_build_filename, 'wb') as f:
        s3.download_fileobj(sm_seed_code_bucket, model_build_sm_seed_code_object_name, f)

    # #Get Model Deploy Seed Code from S3 for Gitlab Repo
    with open(model_deploy_filename, 'wb') as f:
        s3.download_fileobj(sm_seed_code_bucket, model_deploy_sm_seed_code_object_name, f)
 
    #Extract Zip file of seed code to local dir
    try:
        with zipfile.ZipFile(model_build_filename) as z:
            z.extractall(model_build_directory)
            logging.info("Extracted all")
    except:
        logging.error("Invalid file")

    try:
        with zipfile.ZipFile(model_deploy_filename) as z:
            z.extractall(model_deploy_directory)
            logging.info("Extracted all")
    except:
        logging.error("Invalid file")
 
    #Iterate through all of the files in the extracted folder to create commmit data
    build_data = {"branch": "main", "commit_message": "Initial Commit", "actions": []}
    deploy_data = {"branch": "main", "commit_message": "Initial Commit", "actions": []}
 
    for path, _, files in os.walk(model_build_directory): 
        for name in files:
            full_file_path = os.path.join(path, name)
            if name.endswith('.DS_Store'):
                continue
            if name.startswith('._'):
                continue
            else:
                dir = model_build_directory + "/"
                try:
                    build_action = {"action": "create", "file_path": full_file_path.split(dir)[1], "content": open(full_file_path).read()}
                    build_data["actions"].append(build_action)
                except:
                    pass

    for path, _, files in os.walk(model_deploy_directory): 
        for name in files:
            full_file_path = os.path.join(path, name)
            if name.endswith('.DS_Store'):
                continue
            if name.startswith('._'):
                continue
            else:
                dir = model_deploy_directory + "/"
                try:
                    deploy = {"action": "create", "file_path": full_file_path.split(dir)[1], "content": open(full_file_path).read()}
                    deploy_data["actions"].append(deploy)
                except:
                    pass

    try:
        #Create the GitLab Project
        build_project = gl.projects.create({'name': gitlab_project_name_build})
        deploy_project = gl.projects.create({'name': gitlab_project_name_deploy})

        #Commit to the above created Repo all the files that were in the seed code Zip
        build_project.commits.create(build_data)
        deploy_project.commits.create(deploy_data)
        
        build_project.variables.create({'key':'SAGEMAKER_PROJECT_NAME', 'value' : os.environ['SageMakerProjectName']})
        build_project.variables.create({'key':'SAGEMAKER_PROJECT_ID', 'value' : os.environ['SageMakerProjectId']})
        build_project.variables.create({'key':'AWS_REGION', 'value' : region})
        build_project.variables.create({'key':'ARTIFACT_BUCKET', 'value' : 'sagemaker-project-' + os.environ['SageMakerProjectId']})
        build_project.variables.create({'key':'SAGEMAKER_PROJECT_ARN', 'value':'arn:aws:sagemaker:' + region + ':' + os.environ['AccountId'] + ':project/' + os.environ['SageMakerProjectName']})
        build_project.variables.create({'key':'SAGEMAKER_PIPELINE_ROLE_ARN', 'value' : os.environ['Role']})

        deploy_project.variables.create({'key':'SAGEMAKER_PROJECT_NAME', 'value' : os.environ['SageMakerProjectName']})
        deploy_project.variables.create({'key':'SAGEMAKER_PROJECT_ID', 'value' : os.environ['SageMakerProjectId']})
        deploy_project.variables.create({'key':'AWS_REGION', 'value' : region})
        deploy_project.variables.create({'key':'ARTIFACT_BUCKET', 'value' : 'sagemaker-project-' + os.environ['SageMakerProjectId']})
        deploy_project.variables.create({'key':'SAGEMAKER_PROJECT_ARN', 'value':'arn:aws:sagemaker:' + region + ':' + os.environ['AccountId'] + ':project/' + os.environ['SageMakerProjectName']})
        deploy_project.variables.create({'key':'MODEL_EXECUTION_ROLE_ARN', 'value' : os.environ['Role']})

        cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
    except Exception as e:
        logging.debug("The Project could not be created using the GitLab API..")
        logging.debug(e)
        cfnresponse.send(event, context, cfnresponse.FAILED, {})