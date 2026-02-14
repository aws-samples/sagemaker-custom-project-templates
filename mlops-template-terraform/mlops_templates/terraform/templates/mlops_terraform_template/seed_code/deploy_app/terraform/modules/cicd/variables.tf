variable "prefix" {
  type        = string
  description = "Namespace prefix from the template."
}

variable "sm_project_id" {
  type        = string
  description = "Sagemaker Project ID"
}

variable "sm_project_name" {
  type        = string
  description = "Sagemaker Project Name"
}

variable "model_package_group_name" {
  type        = string
  description = "Sagemaker Model Package Group Name"
}

variable "sagemaker_execution_role" {
  type        = string
  description = "Sagemaker Model execution role"
}

variable "target_branch" {
  type        = string
  description = "Branch to connect CICD pipeline to."
}

variable "artifact_bucket_name" {
  type        = string
  description = "Artifact bucket name."
}

variable "pipeline_name" {
  type        = string
  description = "Codepipeline name."
}

variable "codecommit_id" {
  type        = string
  description = "CodeCommit ID."
}


variable "build_timeout" {
  description = "The time to wait for a CodeBuild to complete before timing out in minutes (default: 15)"
  default     = "15"
}

variable "build_compute_type" {
  description = "The build instance type for CodeBuild (default: BUILD_GENERAL1_SMALL)"
  default     = "BUILD_GENERAL1_SMALL"
}

variable "build_image" {
  description = "The build image for CodeBuild to use (default: aws/codebuild/amazonlinux2-x86_64-standard:3.0)"
  default     = "aws/codebuild/amazonlinux2-x86_64-standard:3.0"
}

variable "build_privileged_override" {
  description = "Set the build privileged override to 'true' if you are not using a CodeBuild supported Docker base image. This is only relevant to building Docker images"
  default     = "false"
}