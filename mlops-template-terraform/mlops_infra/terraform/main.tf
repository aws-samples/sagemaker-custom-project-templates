locals {
  prefix = "mlops"
  user_profile_names = ["user1", "user2"]
  domain_name = "${local.prefix}-studio-domain"
  kms_key_alias = "${local.prefix}-kms-key"
}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

module "networking" {
  source                    = ".//modules/networking"
  prefix                    = local.prefix
  vpc_cidr_block            = "10.0.0.0/16"
  private_subnet_cidr_block = "10.0.1.0/24"
  public_subnet_cidr_block  = "10.0.0.0/24"
  availability_zone         = "${data.aws_region.current.name}a" # Get rid of this
}

module "kms" {
  source        = ".//modules/kms"
  kms_key_alias = local.kms_key_alias
}

module "iam" {
  source = ".//modules/iam"
  prefix = local.prefix
  kms_key_arn = module.kms.kms_key_arn
}

module "sm_studio" {
  source                = ".//modules/sagemaker_studio"
  domain_name           = local.domain_name
  vpc_id                = module.networking.vpc_id
  subnet_ids            = [module.networking.private_subnet_ids]
  sm_execution_role_arn = module.iam.sm_execution_role_arn
  kms_key_arn           = module.kms.kms_key_arn
  user_profile_names    = local.user_profile_names
}

