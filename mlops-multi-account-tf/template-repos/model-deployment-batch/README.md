## MLOps for SageMaker Batch Inference Deployment

This is a sample code repository for demonstrating how you can organize your code for deploying a Batch inference infrastructure. This code repository is created as part of creating a Project in SageMaker.

This code repository has the code to find the latest approved ModelPackage for the associated ModelPackageGroup and create the model in the pre-prod and prod account (`build.py`). This code repository defines the CloudFormation template which defines the base infrastructure that is needed in the target account and also defines the Cloud formation template for the batch inference pipeline. It also has configuration files associated with `pre-prod` and `prod` stages.

Upon triggering a deployment, GitHub workflow will deploy 2 Eventbridge rules that triggers a Sagemaker Pipeline for Batch inference - `preprod` and `prod`. After the first deployment is completed, the workflow waits for a manual approval step for promotion to the prod stage.

The template provides a starting point for bringing your SageMaker Pipeline development to production. It can be modified and its functionalities can be extended according to the use case, being a fully customizable template.

### Environment secrets and variables

In order to get environment variables from AWS for the workflow execution, it is set environment secrets when the template repository is cloned for the specific project. They are used in the GitHub Action workflow.
The environment secrets are:

AWS_DEV_ACCOUNT_NUMBER: Account ID of the training AWS account

AWS_PROD_ACCOUNT_NUMBER: Account ID of the Production AWS account to where the endpoint is deployed

AWS_PREPROD_ACCOUNT_NUMBER: Account ID of the Pre Production AWS account where the endpoint is deployed

The environment variables are:

AWS_REGION: AWS account region

SAGEMAKER_PIPELINE_ROLE_ARN: IAM role arn to execute the pipeline

SAGEMAKER_PROJECT_ARN: Arn of the SageMaker project

SAGEMAKER_PROJECT_ID: ID of the SageMaker project

SAGEMAKER_PROJECT_NAME_ID: Name +ID of the SageMaker project

SAGEMAKER_PROJECT_NAME: Name of the SageMaker project



### Repository structure

```
|-- .github/workflows
|   |-- deploy.yml
|-- pipelines
|   |-- run_pipeline.py
|   |-- get_pipeline_definition.py
|   |-- _utils.py
|   |-- _version_.py
|   |-- _init_.py
|   |-- README.md
|   |-- batch_inference
|   |   |-- README.md
|   |   |-- pipeline.py
|   |   |-- preprocess.py
|-- README.md
|-- batch-config-template.tf
|-- build.py
|-- utils.py
|-- pre-prod-config.tfvars.json
`-- prod-config.tfvars.json
```

A description of some of the artifacts is provided below.

```
|-- .github/workflows
|   |-- deploy.yml
```

- This file is used by the GitHub Action to deploy the endpoint in the target account, preprod and prod.
  It is triggered on dispatch, when a manual run is set from the Lambda when the SageMaker Model Package is approved and on push.
  The workflow is divided in two jobs, the first one creates the deployment in the preprod target account and once deployed it waits for the manual approval to execute the second job to deploy in the prod account. Both jobs follow the same steps, the difference is the target account they are pointing to.

The steps are:

- Install the requirements
- Assume OIDC IAM Role in Training account
- Save AWS profile for Training account
- Assume OIDC IAM Role in Target account
- Save AWS profile for Target account
- Deploy/Update base infra to target account
- Deploy to target account the model and the sagemaker pipeline


```
|-- build.py
```

- This python file contains code to get the latest approved model version of the project. Then, checks if the version is already in the target account, in case is not, it uploads the model artifact for that version in the S3 created with the base infra and creates the Model Package in the target account.
The parameters set in the build.py are added into de config.json for the target account. They are used as input parameters into the CloudFormation template.
It is also created the sagemaker pipeline definition from get_pipeline_definition and uploaded to `pipelinedefinition.json`. This pipeline definition is used for creating the pipeline in CloudFormation.


```
|-- utils.py
```

- This file contains the necessary functions for build.py

```
|-- batch_inference
```
- This folder contains SageMaker Pipeline definitions and helper scripts to either simply "get" a SageMaker Pipeline definition (JSON dictionnary) with `get_pipeline_definition.py`, or "run" a SageMaker Pipeline from a SageMaker pipeline definition with `run_pipeline.py`.

Each SageMaker Pipeline definition should be be treated as a module inside its own folder, for example here the "batch_inference" pipeline, contained inside `batch_inference/`.

This SageMaker Pipeline definition creates a workflow that will:
- Prepare the inference dataset through a SageMaker Processing Job
- Run the inference with a Batch transform job

`batch-config-template.tf`

- This Terraform template file is packaged by the deploy step in the Github Actions and is deployed in different stages, pre-prod and prod. Contains the resources: Sagemaker model, Sagemaker Pipeline, Event rule to trigger the pipeline in a schedule and a dashboard to visualize the batch inference events.

`pre-prod-config.tfvars.json`

- This configuration file is used to customize `preprod` stage in the pipeline. You can configure the instance type, instance count here.

`prod-config.tfvars.json`

- This configuration file is used to customize `prod` stage in the pipeline. You can configure the instance type, instance count here.


<!-- BEGIN_AUTOMATED_TF_DOCS_BLOCK -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | 1.5.2 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | ~> 5.15.0 |

## Usage
Basic usage of this module is as follows:
```hcl
module "example" {
	 source  = "<module-path>"

	 # Required variables
	 BatchPipeline  = 
	 Environment  = 
	 InferenceInstanceCount  = 
	 InferenceInstanceType  = 
	 ModelPackageName  = 
	 PipelineDefinitionS3Key  = 
	 ProcessingInstanceCount  = 
	 ProcessingInstanceType  = 
	 ProjectBucket  = 
	 SGIds  = 
	 SageMakerProjectId  = 
	 SageMakerProjectName  = 
	 SubnetIds  = 
	 region  = 

	 # Optional variables
	 ScheduleExpressionforPipeline  = "1 day"
}
```
## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | ~> 5.15.0 |
| <a name="provider_random"></a> [random](#provider\_random) | n/a |
## Modules

No modules.
## Resources

| Name | Type |
|------|------|
| [aws_cloudwatch_dashboard.main](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_dashboard) | resource |
| [aws_cloudwatch_event_rule.sagemaker_pipeline_event_rule](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_event_rule) | resource |
| [aws_cloudwatch_event_target.sagemaker_pipeline_event_target](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_event_target) | resource |
| [aws_sagemaker_model.model](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sagemaker_model) | resource |
| [aws_sagemaker_pipeline.BatchDeployPipeline](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sagemaker_pipeline) | resource |
| [random_id.force_sagemaker_pipeline_update](https://registry.terraform.io/providers/hashicorp/random/latest/docs/resources/id) | resource |
| [aws_caller_identity.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/caller_identity) | data source |
| [aws_region.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/region) | data source |
| [aws_ssm_parameter.sagemaker_role_arn](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/ssm_parameter) | data source |
## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_BatchPipeline"></a> [BatchPipeline](#input\_BatchPipeline) | Name Sagemaker pipeline | `string` | n/a | yes |
| <a name="input_Environment"></a> [Environment](#input\_Environment) | Environment where is deployed | `string` | n/a | yes |
| <a name="input_InferenceInstanceCount"></a> [InferenceInstanceCount](#input\_InferenceInstanceCount) | The number of instance used for inference step | `string` | n/a | yes |
| <a name="input_InferenceInstanceType"></a> [InferenceInstanceType](#input\_InferenceInstanceType) | The type of instance used for inference | `string` | n/a | yes |
| <a name="input_ModelPackageName"></a> [ModelPackageName](#input\_ModelPackageName) | ARN model to deploy | `string` | n/a | yes |
| <a name="input_PipelineDefinitionS3Key"></a> [PipelineDefinitionS3Key](#input\_PipelineDefinitionS3Key) | S3 bucket key where the pipeline definition is stored | `string` | n/a | yes |
| <a name="input_ProcessingInstanceCount"></a> [ProcessingInstanceCount](#input\_ProcessingInstanceCount) | The number of instance used for preprocessing step | `string` | n/a | yes |
| <a name="input_ProcessingInstanceType"></a> [ProcessingInstanceType](#input\_ProcessingInstanceType) | The type of instance used for preprocessing | `string` | n/a | yes |
| <a name="input_ProjectBucket"></a> [ProjectBucket](#input\_ProjectBucket) | S3 bucket sagemaker project | `string` | n/a | yes |
| <a name="input_SGIds"></a> [SGIds](#input\_SGIds) | List security groups | `any` | n/a | yes |
| <a name="input_SageMakerProjectId"></a> [SageMakerProjectId](#input\_SageMakerProjectId) | SageMaker project id | `string` | n/a | yes |
| <a name="input_SageMakerProjectName"></a> [SageMakerProjectName](#input\_SageMakerProjectName) | SageMaker project name | `string` | n/a | yes |
| <a name="input_ScheduleExpressionforPipeline"></a> [ScheduleExpressionforPipeline](#input\_ScheduleExpressionforPipeline) | The rate of execution of your pipeline (default 1 day) | `string` | `"1 day"` | no |
| <a name="input_SubnetIds"></a> [SubnetIds](#input\_SubnetIds) | List private subents | `any` | n/a | yes |
| <a name="input_region"></a> [region](#input\_region) | AWS Region | `string` | n/a | yes |
## Outputs

No outputs.
<!-- END_AUTOMATED_TF_DOCS_BLOCK -->