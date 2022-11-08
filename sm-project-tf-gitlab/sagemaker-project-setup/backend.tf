#---------------------------------------------------------#
# This component has the Backend details to store the State
#---------------------------------------------------------#

terraform {
  backend "s3" {
    bucket               = "dev-machine-learning-ops-<acct-id>" # Based on the default values in the .tfvars files.
    key                  = "mlops.tfstate"
    workspace_key_prefix = ""
    region               = "us-region-1"
    dynamodb_table       = "terraform-tfstate-dev-<acct-id>" # Based on the default values in the .tfvars files.
    encrypt              = true
  }
}