import os
import boto3
import json
import botocore

region = boto3.Session().region_name
sm_client = boto3.client('sagemaker', region_name=region)

sagemaker_code_config = open('.sagemaker-code-config')
config = json.load(sagemaker_code_config)
model_package_group_name = config["model_package_group_name"]

mpg = sm_client.list_model_packages(ModelPackageGroupName=model_package_group_name)

mpsl = mpg["ModelPackageSummaryList"]
last_approved_model = None
for model_package in mpsl:
    approval_status = model_package["ModelApprovalStatus"]
    model_arn = model_package["ModelPackageArn"]
    # print(f'version:{model_package["ModelPackageVersion"]}\tapproval:{approval_status}\tarn:{model_arn}')
    if last_approved_model is None and approval_status == "Approved":
        last_approved_model = model_arn

try:
    model_response = sm_client.describe_model_package(
        ModelPackageName=last_approved_model
    )
    inference_image = model_response['InferenceSpecification']['Containers'][0]['Image']
    model_data_url = model_response['InferenceSpecification']['Containers'][0]['ModelDataUrl']

except botocore.exceptions.ParamValidationError as e:
    if 'Invalid type for parameter ModelPackageName, value: None' in str(e):
        inference_image = 'None'
        model_data_url = 'None'
    else:
        raise e

tf_vars_data =  f'''inference_image = "{inference_image}"
model_data_url = "{model_data_url}"'''

with open('terraform/model.auto.tfvars', 'w') as f:
    f.write(tf_vars_data)

print(f"Last Approved Model: {last_approved_model}")