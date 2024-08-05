terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.12.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "3.5.1"
    }
    tfe = {
      source  = "hashicorp/tfe"
      version = "0.45.0"
    }
  }
}

provider "aws" {
  default_tags {
    tags = {
      "Projects" = "mlops-terraform-cloud"
    }
  }
}

provider "tfe" {
  hostname = var.tfc_hostname
}

# This module provisions the Terraform Cloud Reference Engine. If you would like to provision the Reference Engine
# without the example product, you can use this module in your own terraform configuration/workspace.
module "terraform_cloud_reference_engine" {
  source = "./aws-service-catalog-engine-for-tfc/engine"

  tfc_organization                 = var.tfc_organization
  tfc_team                         = var.tfc_team
  tfc_aws_audience                 = var.tfc_aws_audience
  tfc_hostname                     = var.tfc_hostname
  cloudwatch_log_retention_in_days = var.cloudwatch_log_retention_in_days
  enable_xray_tracing              = var.enable_xray_tracing
  token_rotation_interval_in_days  = var.token_rotation_interval_in_days
  terraform_version                = var.terraform_version
}

# Creates an AWS Service Catalog Portfolio to house the example product
resource "aws_servicecatalog_portfolio" "portfolio" {
  name          = "TFC MLOps Portfolio"
  description   = "Portfolio created via AWS Service Catalog Engine for TFC"
  provider_name = "AWS"
}

# An example product
module "mlops_product" {
  source = "./mlops-product"

  # ARNs of Lambda functions that need to be able to assume the IAM Launch Role
  parameter_parser_role_arn  = module.terraform_cloud_reference_engine.parameter_parser_role_arn
  send_apply_lambda_role_arn = module.terraform_cloud_reference_engine.send_apply_lambda_role_arn
  sagemaker_user_role_arns   = var.sagemaker_user_role_arns

  # AWS Service Catalog portfolio you would like to add this product to
  service_catalog_portfolio_ids = [aws_servicecatalog_portfolio.portfolio.id]

  # Variables for authentication to AWS via Dynamic Credentials
  tfc_hostname     = module.terraform_cloud_reference_engine.tfc_hostname
  tfc_organization = module.terraform_cloud_reference_engine.tfc_organization
  tfc_provider_arn = module.terraform_cloud_reference_engine.oidc_provider_arn

}
