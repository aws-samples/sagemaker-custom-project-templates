locals {
  prefix = "mlops"
  templates = {
    mlops_terraform_template : {
      name : "${local.prefix}_terraform_template"
      owner : "central-IT"
      template_key        = "${local.prefix}/resouces/service_catalog/templates/terraform_template/service_catalog_product_template.yaml"
      template_local_path = "./templates/mlops_terraform_template/service_catalog_product_template.yaml.tpl"
      seed_code_map : {
        "build" : {
          local_path : "./templates/mlops_terraform_template/seed_code/build_app"
          key : "${local.prefix}/resouces/service_catalog/seed_code/terraform_template/build.zip"
        },
        "deploy" : {
          local_path : "./templates/mlops_terraform_template/seed_code/deploy_app",
          key : "${local.prefix}/resouces/service_catalog/seed_code/terraform_template/deploy.zip"
        }
      }
    }
  }
}


data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

module "sm_project_template" {
  source                       = ".//modules/sagemaker_project_template"
  template_name                = local.templates.mlops_terraform_template.name
  owner                        = local.templates.mlops_terraform_template.owner
  sagemaker_execution_role_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${local.prefix}-sagemaker-execution-role"
  seed_code_map                = local.templates.mlops_terraform_template.seed_code_map
  template_local_path          = local.templates.mlops_terraform_template.template_local_path
  template_key                 = local.templates.mlops_terraform_template.template_key

  # These values will be injected into the template.yaml file. 
  # The $${} escape allows referencing CloudFormation Parameters
  template_vars = {
    prefix = local.prefix
    artifact_bucket_name = "${local.prefix}-project-$${SageMakerProjectName}"
    state_bucket_name = "${local.prefix}-project-$${SageMakerProjectName}-tf-state"
    build_code_repo_name = "${local.prefix}-project-$${SageMakerProjectName}-modelbuild"
    deploy_code_repo_name = "${local.prefix}-project-$${SageMakerProjectName}-modeldeploy"
    seed_code_build_key  = local.templates.mlops_terraform_template.seed_code_map["build"].key,
    seed_code_deploy_key = local.templates.mlops_terraform_template.seed_code_map["deploy"].key,
    default_branch = "main"
  }
}

