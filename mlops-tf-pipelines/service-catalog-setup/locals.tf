#----------------------------------------#
# This component has all the Local values
#----------------------------------------#

locals {

  # Account ID  
  account_id = data.aws_caller_identity.current.account_id

  # Common Resource Name  
  cmn_res_name = "${var.env}-${var.organization}-${var.role}"

  # Folder of the SageMaker Project CFN template  
  cfn_folder = "cfn-source"
  cfn_sm_key = "sm-project-cfn.yaml"

  # Terraform Code Folder for the SageMaker Projects  
  sm_project_folder = "../sagemaker-project-setup"
  source_files      = ["${local.sm_project_folder}/main.tf"]

  # Output zip artifacts for the Terraform SageMaker Project Code  
  output_files         = "tf-code-zip"
  output_tf_zip_folder = "tf-code"

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