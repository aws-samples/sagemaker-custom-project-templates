module "sagemaker_projects_bucket" {
  source                  = "../modules/s3"
  s3_bucket_name          = "ml-artifacts-${local.aws_region}-${local.account_id}"
  s3_bucket_force_destroy = "false"
  versioning              = "Enabled"
  s3_bucket_policy        = data.aws_iam_policy_document.s3_projects_bucket_policy.json
}


module "kms" {
  source                              = "../modules/kms"
  trusted_accounts_for_decrypt_access = [var.preprod_account_number, var.prod_account_number]
  account_id                          = local.account_id
}

# Networking resources (VPC, endpoints)
module "networking" {
  source = "../modules/networking"
  region = var.region
}
