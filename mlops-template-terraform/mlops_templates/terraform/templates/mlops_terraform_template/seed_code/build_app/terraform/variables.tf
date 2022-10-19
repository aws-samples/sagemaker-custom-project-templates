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



