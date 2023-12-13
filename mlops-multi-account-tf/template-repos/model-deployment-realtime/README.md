## MLOps for SageMaker Endpoint Deployment


This is a sample code repository for demonstrating how you can organize your code for deploying a realtime inference Endpoint infrastructure. This code repository is created as part of creating a Project in SageMaker.

This code repository has the code to find the latest approved ModelPackage for the associated ModelPackageGroup and create the model in the pre-prod and prod account (`build.py`). This code repository defines the CloudFormation template which defines the base infrastructure that is needed in the target account and also defines the Cloud formation template for the endpoints creation. It also has configuration files associated with `pre-prod` and `prod` stages.

Upon triggering a deployment, GitHub workflow will deploy 2 Endpoints - `staging` and `prod`. After the first deployment is completed, the workflow waits for a manual approval step for promotion to the prod stage.

The template provides a starting point for bringing your SageMaker Pipeline development to production. It can be modified and its functionalities can be extended according to the use case, being a fully customizable template.

### Environment secrets

In order to get environment variables from AWS for the workflow execution, it is set environment secrets when the template repository is cloned for the specific project. They are used in the GitHub Action workflow.
The environment secrets are:

`AWS_REGION`: AWS account region

`SAGEMAKER_PIPELINE_ROLE_ARN`: IAM role arn to execute the pipeline

`SAGEMAKER_PROJECT_ARN`: Arn of the SageMaker project

`SAGEMAKER_PROJECT_ID`: ID of the SageMaker project

`SAGEMAKER_PROJECT_NAME_ID`: Name +ID of the SageMaker project

`SAGEMAKER_PROJECT_NAME`: Name of the SageMaker project

`AWS_DEV_ACCOUNT_NUMBERR`: Account ID of the training AWS account

`AWS_PROD_ACCOUNT_NUMBER`: Account ID of the Production AWS account to where the endpoint is deployed

`AWS_PREPROD_ACCOUNT_NUMBER`: Account ID of the Pre Production AWS account where the endpoint is deployed

### Repository structure

```
|-- .github/workflows
|   |-- deploy.yml
|-- infra
|   |-- infra.yaml
|-- README.md
|-- endpoint-config-template.tf
|-- build.py
|-- utils.py
|-- test
|   `-- test.py
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
- Deploy to target account the model and the endpoint
- Test target account deployment

```
|-- infra
|   |-- infra.yaml
```

- This file deploys the base infrastructure for the target account, pre-prod and prod. Creates the IAM role to be assumed by the endpoint and the S3 bucket to store

```
|-- build.py
```

- This python file contains code to get the latest approved model version of the project. Then, checks if the version is already in the target account, in case is not, it uploads the model artifact for that version in the S3 created with the base infra and creates the Model Package in the target account.
  The parameters set in the build.py are added into de config.json for the target account. They are used as input parameters into the CloudFormation template.

```
|-- utils.py
```

- this file contains the necessary functions for build.py

`endpoint-config-template.tf`

- this Terraform template file is packaged by the deploy step in the Github Actions and is deployed in different stages, pre-prod and prod. Contains the resources: Sagemaker model, endpoint config y endpoint. In addition, it is possible to add the endpoint into a VPC

`pre-prod-config.tfvars.json`

- this configuration file is used to customize `staging` stage in the pipeline. You can configure the instance type, instance count here.

`prod-config.tfvars.json`

- this configuration file is used to customize `prod` stage in the pipeline. You can configure the instance type, instance count here.

`test\test.py`

- this python file contains code to describe and invoke the staging endpoint. You can customize to add more tests here.

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
	 EndpointInstanceCount  = 
	 EndpointInstanceType  = 
	 Environment  = 
	 ModelPackageName  = 
	 ProjectBucket  = 
	 SGIds  = 
	 SageMakerProjectId  = 
	 SageMakerProjectName  = 
	 SamplingPercentage  = 
	 SubnetIds  = 
	 region  = 

	 # Optional variables
	 EnableDataCapture  = "true"
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
| [aws_sagemaker_endpoint.sm_endpoint](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sagemaker_endpoint) | resource |
| [aws_sagemaker_endpoint_configuration.sm_endpoint_configuration](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sagemaker_endpoint_configuration) | resource |
| [aws_sagemaker_model.model_rt_inference](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sagemaker_model) | resource |
| [random_id.force_endpoint_update](https://registry.terraform.io/providers/hashicorp/random/latest/docs/resources/id) | resource |
| [aws_caller_identity.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/caller_identity) | data source |
| [aws_region.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/region) | data source |
| [aws_ssm_parameter.sagemaker_role_arn](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/ssm_parameter) | data source |
## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_EnableDataCapture"></a> [EnableDataCapture](#input\_EnableDataCapture) | Enable Data capture | `string` | `"true"` | no |
| <a name="input_EndpointInstanceCount"></a> [EndpointInstanceCount](#input\_EndpointInstanceCount) | Number of instances to launch for the endpoint. | `string` | n/a | yes |
| <a name="input_EndpointInstanceType"></a> [EndpointInstanceType](#input\_EndpointInstanceType) | The ML compute instance type for the endpoint. | `string` | n/a | yes |
| <a name="input_Environment"></a> [Environment](#input\_Environment) | Environment where is deployed | `string` | n/a | yes |
| <a name="input_ModelPackageName"></a> [ModelPackageName](#input\_ModelPackageName) | ARN model to deploy | `string` | n/a | yes |
| <a name="input_ProjectBucket"></a> [ProjectBucket](#input\_ProjectBucket) | S3 bucket sagemaker project | `string` | n/a | yes |
| <a name="input_SGIds"></a> [SGIds](#input\_SGIds) | List security groups | `any` | n/a | yes |
| <a name="input_SageMakerProjectId"></a> [SageMakerProjectId](#input\_SageMakerProjectId) | SageMaker project id | `string` | n/a | yes |
| <a name="input_SageMakerProjectName"></a> [SageMakerProjectName](#input\_SageMakerProjectName) | SageMaker project name | `string` | n/a | yes |
| <a name="input_SamplingPercentage"></a> [SamplingPercentage](#input\_SamplingPercentage) | The sampling percentage | `number` | n/a | yes |
| <a name="input_SubnetIds"></a> [SubnetIds](#input\_SubnetIds) | List private subents | `any` | n/a | yes |
| <a name="input_region"></a> [region](#input\_region) | AWS Region | `string` | n/a | yes |
## Outputs

No outputs.
<!-- END_AUTOMATED_TF_DOCS_BLOCK -->
