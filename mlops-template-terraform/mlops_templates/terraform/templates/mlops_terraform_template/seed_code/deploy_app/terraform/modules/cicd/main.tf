locals {
  prefix = var.prefix
  sm_project_id        = var.sm_project_id
  sm_project_name      = var.sm_project_name
  model_package_group_name        = var.model_package_group_name
  pipeline_name                   = var.pipeline_name
  target_branch        = var.target_branch
  codecommit_id        = var.codecommit_id
  artifact_bucket_name = var.artifact_bucket_name
  build_compute_type        = var.build_compute_type
  build_image               = var.build_image
  build_timeout             = var.build_timeout
  build_privileged_override = var.build_privileged_override
  sagemaker_execution_role  = var.sagemaker_execution_role
}

data "aws_caller_identity" "current" {}

data "aws_codecommit_repository" "repo" {
  repository_name = local.codecommit_id
}

data "aws_kms_alias" "s3" {
  name = "alias/aws/s3"
}

