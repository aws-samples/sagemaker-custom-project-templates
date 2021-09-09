import boto3
import json
import os

cloud_formation = boto3.client('cloudformation')


def lambda_handler(event, context):
    repository_name: str = event['detail']['repositoryName']
    branch_name: str = event['detail']['referenceName']
    branch_name_norm = branch_name.replace('/', '-')

    pipeline_name = f'{repository_name}-{branch_name_norm}'

    response = cloud_formation.delete_stack(
        StackName=pipeline_name,
        RoleARN=os.getenv('CLOUD_FORMATION_ROLE_ARN'),
    )

    print(response)
