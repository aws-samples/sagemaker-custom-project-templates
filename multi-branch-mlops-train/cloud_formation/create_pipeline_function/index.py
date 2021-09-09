import boto3
import os
import json
import io

cloud_formation = boto3.client('cloudformation')
s3_client = boto3.client('s3')


def get_s3_object(bucket_name: str, key: str) -> str:
    buf = io.BytesIO()
    s3_client.download_fileobj(Bucket=bucket_name, Key=key, Fileobj=buf)
    return buf.getvalue().decode()


def lambda_handler(event, context):
    repository_name: str = event['detail']['repositoryName']
    branch_name: str = event['detail']['referenceName']

    if 'experiment' not in branch_name:
        print('skipping pipeline creation because branch is not experiment')
        return

    branch_name_norm = branch_name.replace('/', '-')

    pipeline_name = f'{repository_name}-{branch_name_norm}'

    template_body = get_s3_object(
        bucket_name=os.getenv('PIPELINE_STACK_S3_BUCKET'),
        key=os.getenv('PIPELINE_STACK_S3_KEY')
    )

    response = cloud_formation.create_stack(
        StackName=pipeline_name,
        TemplateBody=template_body,
        Parameters=[
            {
                'ParameterKey': 'BranchName',
                'ParameterValue': branch_name,
            },
            {
                'ParameterKey': 'BranchNameNorm',
                'ParameterValue': branch_name_norm
            },
            {
                'ParameterKey': 'ModelName',
                'ParameterValue': os.getenv('MODEL_NAME'),
            },
            {
                'ParameterKey': 'RepositoryName',
                'ParameterValue': repository_name,
            },
            {
                'ParameterKey': 'CodePipelineArtifactBucket',
                'ParameterValue': os.getenv('CODE_PIPELINE_ARTIFACT_BUCKET'),
            },
            {
                'ParameterKey': 'CodePipelineRoleArn',
                'ParameterValue': os.getenv('CODE_PIPELINE_ROLE_ARN'),
            },
            {
                'ParameterKey': 'CodePipelineSourceActionRoleArn',
                'ParameterValue': os.getenv('CODE_PIPELINE_SOURCE_ACTION_ROLE_ARN'),
            },
            {
                'ParameterKey': 'CodePipelineBuildActionRoleArn',
                'ParameterValue': os.getenv('CODE_PIPELINE_BUILD_ACTION_ROLE_ARN'),
            },
            {
                'ParameterKey': 'EventStartPipelineRoleArn',
                'ParameterValue': os.getenv('EVENT_START_PIPELINE_ROLE_ARN'),
            },
            {
                'ParameterKey': 'CodeBuildProjectName',
                'ParameterValue': os.getenv('CODE_BUILD_PROJECT_NAME'),
            },
        ],
        TimeoutInMinutes=5,
        Capabilities=[
            'CAPABILITY_IAM',
        ],
        RoleARN=os.getenv('CLOUD_FORMATION_ROLE_ARN'),
    )

    print(response)
