locals {
  prefix = var.prefix
  sm_project_id  = var.sm_project_id
  sm_project_name = var.sm_project_name
  aws_account_id = var.aws_account_id
  aws_region     = var.aws_region
  target_branch  = var.default_branch
  artifact_bucket_name = var.artifact_bucket_name
  codecommit_id  = var.codecommit_id
  initial_instance_count = 1
  initial_sampling_percentage = 30
  initial_variant_weight = 1
  instance_type = "ml.t2.medium"
  model_name = "${local.sm_project_name}-model"
  sagemaker_endpoint_configuration_name = "${local.prefix}-${local.sm_project_name}-config"
  sagemaker_endpoint_name = "${local.prefix}-${local.sm_project_name}-endpoint"
  variant_name = "v1"
  sagemaker_execution_role = var.sm_execution_role_arn
  inference_image = var.inference_image
  model_data_url = var.model_data_url
  pipeline_name = "modeldeploy-pipeline"
  model_package_group_name = var.model_package_group_name
}


module "cicd_build_pipeline" {
  source = ".//modules/cicd"

  prefix = local.prefix
  sm_project_id        = local.sm_project_id
  sm_project_name      = local.sm_project_name
  model_package_group_name = local.model_package_group_name
  codecommit_id        = local.codecommit_id
  target_branch        = local.target_branch
  artifact_bucket_name = local.artifact_bucket_name
  pipeline_name        = local.pipeline_name
  sagemaker_execution_role = local.sagemaker_execution_role
}

module "sm_endpoint_slim" {
  source = ".//modules/sm_endpoint_slim"
  
  count = "${local.inference_image == "None" ? 0 : 1}"
  prefix = local.prefix
  instance_type = local.instance_type
  initial_instance_count = local.initial_instance_count
  model_name = local.model_name
  sagemaker_execution_role = local.sagemaker_execution_role
  sagemaker_endpoint_name = local.sagemaker_endpoint_name
  variant_name = local.variant_name
  inference_image = local.inference_image
  model_data_url = local.model_data_url
}