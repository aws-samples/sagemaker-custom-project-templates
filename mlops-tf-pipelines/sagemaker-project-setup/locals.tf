#----------------------------------------#
# This component has all the Local values
#----------------------------------------#

locals {

  # Account ID  
  account_id = data.aws_caller_identity.current.account_id

  # Common Resource Name
  cmn_res_name = lower("${var.sagemaker_project_name}-${var.sagemaker_project_id}")

  # SeedCode Lambda Files
  lambda_files = "lambdas-source"
  source_files = ["${local.lambda_files}/app.py"]

  # Lambda Output Zip
  output_files = "lambdas-zip"

  # Tags for Resources  
  common_tags = {
    Terraform         = true
    Organization      = var.organization
    Environment       = var.env
    Role              = var.role
    common_identifier = local.cmn_res_name
    Name              = local.cmn_res_name
  }

}
