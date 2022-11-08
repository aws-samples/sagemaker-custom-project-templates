# Variables
#------------
variable "region" {
  description = "AWS region identifier"
}

variable "env" {
  description = "Name of the environment the infrastructure is for"
}

variable "organization" {
  description = "Name of the organization the infrastructure is for"
}

variable "role" {
  description = "Name or role of the component or subcomponent"
}


variable "sagemaker_service_catalog_codebuild_role" {
  description = "AWS IAM role assigned for AWS CodeBuild"
}

variable "sagemaker_service_catalog_exec_role" {
  description = "AWS IAM role assigned for AmazonSageMaker ServiceCatalog Product"
}


variable "sagemaker_service_catalog_codepipeline_role" {
  description = "AWS IAM role assigned for AWS CodePipeline"
}

variable "sagemaker_service_catalog_events_role" {
  description = "AWS IAM role assigned for AWS CloudWatch Events"
}

variable "sagemaker_service_catalog_lambda_role" {
  description = "AWS IAM role assigned for AWS Lambda Functions"
}

variable "sagemaker_project_name" {
  description = "Amazon Sagemaker Project Name"
}

variable "sagemaker_project_id" {
  description = "Amazon Sagemaker Project Id"
}

variable "codestar_connection_arn" {
  description = "AWS CodeStar connection arn for Github connection"
}

variable "gitlab_url" {
  description = "URL of the Git Repository that will have the model code"
}

variable "git_repo_name" {
  description = "Name of the Git Repository that will have the model code"
}

variable "git_repo_branch" {
  description = "Branch of the Git Repository that will have the model code"
}

variable "secrets_manager_gitlab_secret_name" {
  description = "Secrets Manager Secret having the Gitlab Private Token"
}

variable "secrets_manager_gitlab_iam_access_key" {
  description = "Secrets Manager Secret having the Gitlab IAM Access Key"
}

variable "secrets_manager_gitlab_iam_secret_key" {
  description = "Secrets Manager Secret having the Gitlab IAM Secret Key"
}
