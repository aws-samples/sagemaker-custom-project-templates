import json
import os
import boto3
import traceback

code_pipeline = boto3.client('codepipeline')
sagemaker = boto3.client('sagemaker')


def approve_model_package(model_package_group_name, commit_id):
    response_iterator = sagemaker.get_paginator('list_model_packages').paginate(
        ModelPackageGroupName=model_package_group_name,
        ModelPackageType='Versioned',
        SortBy='CreationTime',
        SortOrder='Descending',
    )
    for response in response_iterator:
        for model_package in response['ModelPackageSummaryList']:
            model_package_arn = model_package['ModelPackageArn']
            model_package_response = sagemaker.describe_model_package(
                ModelPackageName=model_package_arn
            )
            if model_package_response['MetadataProperties']['CommitId'] == commit_id:
                if model_package['ModelApprovalStatus'] == 'Rejected':
                    raise Exception(f'Model package name {model_package_arn} is rejected. Aborting.')
                update_model_package_response = sagemaker.update_model_package(
                    ModelPackageArn=model_package_arn,
                    ModelApprovalStatus='Approved',
                )
                print(f'Approved. Package={model_package}; Response={update_model_package_response}')
                return
    raise Exception(f'Did not find model with commit "{commit_id}" on model package group "{model_package_group_name}"')


def lambda_handler_code_pipeline(event, context):
    job_id = event['CodePipeline.job']['id']
    try:
        user_params = event['CodePipeline.job']['data']['actionConfiguration']['configuration']['UserParameters']
        user_params = json.loads(user_params)

        model_package_group_name = os.getenv('MODEL_PACKAGE_GROUP_NAME')

        approve_model_package(
            model_package_group_name=model_package_group_name,
            commit_id=user_params['commit_id']
        )

        response = code_pipeline.put_job_success_result(
            jobId=job_id,
        )
        print(response)
    except Exception as e:
        traceback.print_exc()
        response = code_pipeline.put_job_failure_result(
            jobId=job_id,
            failureDetails={
                'type': 'JobFailed',
                'message': str(e),
            }
        )
        print(response)


def lambda_handler_jenkins(event, context):
    model_package_group_name = os.getenv('MODEL_PACKAGE_GROUP_NAME')

    approve_model_package(
        model_package_group_name=model_package_group_name,
        commit_id=event['commit_id']
    )


def lambda_handler(event, context):
    if 'CodePipeline.job' in event:
        return lambda_handler_code_pipeline(event, context)
    else:
        return lambda_handler_jenkins(event, context)
