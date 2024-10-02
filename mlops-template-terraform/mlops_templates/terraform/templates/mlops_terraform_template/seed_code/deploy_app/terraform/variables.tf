variable "sm_project_id" {
  type        = string
  description = "Sagemaker Project ID"
}

variable "sm_project_name" {
  type        = string
  description = "Sagemaker Project Name"
}

variable "aws_account_id" {
  type        = string
  description = "AWS Account ID"
}

variable "aws_region" {
  type        = string
  description = "AWS Region"
}

variable "codecommit_id" {
  type        = string
  description = "CodeCommit ID."
}

variable "prefix" {
  type        = string
  description = "Namespace prefix from the template."
}

variable "artifact_bucket_name" {
  type        = string
  description = "Project artifact bucket name."
}

variable "default_branch" {
  type        = string
  description = "Default CodeCommit branch."
}

variable "model_name" {
  type        = string
  description = "SageMaker model name"
  default = ""
}

variable "sm_execution_role_arn" {
  type        = string
  description = "SageMaker Execution role arn"
}

variable "inference_image" {
  type = string
  default = ""
  description = "Model inference image"
}

variable "model_data_url" {
  type        = string
  description = "SageMaker model data url"
  default = ""
}

variable "model_package_group_name" {
  type = string
  description = "Name of project's model package group"
}




