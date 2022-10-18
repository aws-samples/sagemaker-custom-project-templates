#---------------------------------------------------------#
# This component has the Backend details to store the State
#---------------------------------------------------------#

terraform {
  backend "s3" {
    bucket               = "dev-machine-learning-ops-167084800113" # Based on the default values in the .tfvars files.
    key                  = "mlops.tfstate"
    workspace_key_prefix = ""
    region               = "us-west-2"
    dynamodb_table       = "terraform-tfstate-dev-167084800113" # Based on the default values in the .tfvars files.
    encrypt              = true
  }
}