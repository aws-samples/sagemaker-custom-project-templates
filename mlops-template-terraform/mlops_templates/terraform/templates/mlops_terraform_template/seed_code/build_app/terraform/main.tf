locals {
  prefix = var.prefix
  sm_project_id  = var.sm_project_id
  sm_project_name = var.sm_project_name
  aws_account_id = var.aws_account_id
  aws_region     = var.aws_region
  target_branch  = var.default_branch
  codecommit_id  = var.codecommit_id
  artifact_bucket_name = var.artifact_bucket_name
  sm_pipeline_name = "modelbuild-pipeline"
  model_package_group_name = "models"
  pipeline_name = "modelbuild-pipeline"
}

module "cicd_build_pipeline" {
  source = ".//modules/cicd"
  
  prefix = local.prefix
  sm_project_id        = local.sm_project_id
  sm_project_name      = local.sm_project_name
  sm_pipeline_name     = local.sm_pipeline_name
  model_package_group_name = local.model_package_group_name
  codecommit_id        = local.codecommit_id
  target_branch        = local.target_branch
  artifact_bucket_name = local.artifact_bucket_name
  pipeline_name        = local.pipeline_name
}

