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
            return secret.split(':')[-1].strip('"}')
        else:
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
            return decoded_binary_secret
            
    return None

def lambda_handler(event, context):
    ''' '''
    response_data = {}
    if 'RequestType' in event:
        if not (event['RequestType'] == 'Create'):
            cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data)
            return

    sm_seed_code_bucket = os.environ['SeedCodeBucket']
    gitlab_server_uri = os.environ['GitLabServer']
    model_build_sm_seed_code_object_name = os.environ['ModelBuildSeedCode'] 
    model_deploy_sm_seed_code_object_name = os.environ['ModelDeploySeedCode'] 
    region = os.environ['Region']
    
    gitlab_project_name_build = os.environ['BuildProjectName'] + '-' + os.environ['SageMakerProjectId']
    gitlab_project_name_deploy = os.environ['DeployProjectName'] + '-' + os.environ['SageMakerProjectId']
    gitlab_private_token = get_secret() 

    if gitlab_private_token is None:
        raise Exception("GitLab token was not retrieved from Secrets Manager")
 
    # Configure SDKs for GitLab and S3
    gl = gitlab.Gitlab(gitlab_server_uri, private_token=gitlab_private_token)
    s3 = boto3.client('s3')
 
    model_build_filename = f'/tmp/{str(uuid.uuid4())}-model-build-seed-code.zip'
    model_deploy_filename = f'/tmp/{str(uuid.uuid4())}-model-deploy-seed-code.zip'
    model_build_directory = f'/tmp/{str(uuid.uuid4())}-model-build'
    model_deploy_directory = f'/tmp/{str(uuid.uuid4())}-model-deploy'

    # Get Model Build Seed Code from S3 for Gitlab Repo
    with open(model_build_filename, 'wb') as f:
        s3.download_fileobj(sm_seed_code_bucket, model_build_sm_seed_code_object_name, f)

    # Get Model Deploy Seed Code from S3 for Gitlab Repo
    with open(model_deploy_filename, 'wb') as f:
        s3.download_fileobj(sm_seed_code_bucket, model_deploy_sm_seed_code_object_name, f)
 
    # Extract Zip file of seed code to local dir
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
 
    # Iterate through all of the files in the extracted folder to create commmit data
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

    group_id = os.environ["GroupId"]
    if group_id in ['None', 'none']:
        group_id = None
    else:
        group_id = gl.groups.list(search=group_id)[0].id

    # Create the GitLab Project
    try:
        if group_id is None:
            build_project = gl.projects.create({'name': gitlab_project_name_build})
        else:
            build_project = gl.projects.create({'name': gitlab_project_name_build, 'namespace_id': int(group_id)})
    except Exception as e:
        logging.error("The Project could not be created using the GitLab API..")
        logging.error(e)
        cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
        return { 
            'message' : "GitLab seedcode checkin failed."
        }
    
    try:
        if group_id is None:
            deploy_project = gl.projects.create({'name': gitlab_project_name_deploy})
        else:
            deploy_project = gl.projects.create({'name': gitlab_project_name_deploy, 'namespace_id': int(group_id)})
    except Exception as e:
        logging.error("The Project could not be created using the GitLab API..")
        logging.error(e)
        cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
        return { 
            'message' : "GitLab seedcode checkin failed."
        }

    # Commit to the above created Repo all the files that were in the seed code Zip
    try:
        build_project.commits.create(build_data)
    except Exception as e:
        logging.error("Code could not be pushed to the model build repo.")
        logging.error(e)
        cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
        return { 
            'message' : "GitLab seedcode checkin failed."
        }

    try:
        deploy_project.commits.create(deploy_data)
    except Exception as e:
        logging.error("Code could not be pushed to the model deploy repo.")
        logging.error(e)
        cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
        return { 
            'message' : "GitLab seedcode checkin failed."
        }

    # Create project variables in model build and deploy repos
    try:
        build_project.variables.create({'key':'SAGEMAKER_PROJECT_NAME', 'value' : os.environ['SageMakerProjectName']})
        build_project.variables.create({'key':'SAGEMAKER_PROJECT_ID', 'value' : os.environ['SageMakerProjectId']})
        build_project.variables.create({'key':'AWS_REGION', 'value' : region})
        build_project.variables.create({'key':'ARTIFACT_BUCKET', 'value' : 'sagemaker-project-' + os.environ['SageMakerProjectId']})
        build_project.variables.create({'key':'SAGEMAKER_PROJECT_ARN', 'value':'arn:aws:sagemaker:' + region + ':' + os.environ['AccountId'] + ':project/' + os.environ['SageMakerProjectName']})
        build_project.variables.create({'key':'SAGEMAKER_PIPELINE_ROLE_ARN', 'value' : os.environ['Role']})
    except Exception as e:
        logging.error("Project variables could not be created for model build")
        logging.error(e)
        cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
        return { 
            'message' : "GitLab seedcode checkin failed."
        }

    try:
        deploy_project.variables.create({'key':'SAGEMAKER_PROJECT_NAME', 'value' : os.environ['SageMakerProjectName']})
        deploy_project.variables.create({'key':'SAGEMAKER_PROJECT_ID', 'value' : os.environ['SageMakerProjectId']})
        deploy_project.variables.create({'key':'AWS_REGION', 'value' : region})
        deploy_project.variables.create({'key':'ARTIFACT_BUCKET', 'value' : 'sagemaker-project-' + os.environ['SageMakerProjectId']})
        deploy_project.variables.create({'key':'SAGEMAKER_PROJECT_ARN', 'value':'arn:aws:sagemaker:' + region + ':' + os.environ['AccountId'] + ':project/' + os.environ['SageMakerProjectName']})
        deploy_project.variables.create({'key':'MODEL_EXECUTION_ROLE_ARN', 'value' : os.environ['Role']})
    except Exception as e:
        logging.error("Project variables could not be created for model deploy")
        logging.error(e)
        cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
        return { 
            'message' : "GitLab seedcode checkin failed."
        }

    logger.info("Successfully checked in seed code to GitLab..")
    cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data)
    
    return { 
        'message' : "GitLab seedcode checkin successfully completed"
    }
