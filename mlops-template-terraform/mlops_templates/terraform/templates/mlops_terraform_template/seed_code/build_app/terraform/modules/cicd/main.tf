locals {
  prefix = var.prefix
  sm_project_id        = var.sm_project_id
  sm_project_name      = var.sm_project_name
  sm_pipeline_name                = "${local.prefix}-${local.sm_project_name}-${var.sm_pipeline_name}"
  sm_pipeline_execution_role_name = "${local.prefix}-${replace(local.sm_project_id, "_", "-")}-pipeline-exec-build"
  model_package_group_name        = "${local.prefix}-${local.sm_project_name}-${var.model_package_group_name}"
  pipeline_name                   = "${local.prefix}-${local.sm_project_name}-${var.pipeline_name}"
  codecommit_id        = var.codecommit_id
  target_branch        = var.target_branch
  artifact_bucket_name = var.artifact_bucket_name
  build_compute_type        = var.build_compute_type
  build_image               = var.build_image
  build_timeout             = var.build_timeout
  build_privileged_override = var.build_privileged_override
}

data "aws_caller_identity" "current" {}

data "aws_codecommit_repository" "repo" {
  repository_name = local.codecommit_id
}

data "aws_kms_alias" "s3" {
  name = "alias/aws/s3"
}


