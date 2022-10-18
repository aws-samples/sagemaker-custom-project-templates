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

variable "seed_code_s3_location" {
  description = "location of seed code used in codebuild that will copy model seed code to the git repo "
}

variable "seed_code_bucket_name" {
  description = "s3 bucket name containing the model seed code to the git repo "
}

variable "seed_code_bucket_key" {
  description = "s3 bucket key containing the model seed code to the git repo "
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

variable "git_repo_url" {
  description = "URL of the Git Repository that will have the model code"
}

variable "git_repo_name" {
  description = "Name of the Git Repository that will have the model code"
}

variable "git_repo_branch" {
  description = "Branch of the Git Repository that will have the model code"
}

variable "secrets_manager_secret_arn" {
  description = "ARN of the Secrets Manager Secret having the GIT Repo credentials"
}


