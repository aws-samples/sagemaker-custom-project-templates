#---------------------------------------------------------#
# This component has the Backend details to store the State
#---------------------------------------------------------#

terraform {
  backend "s3" {
    bucket               = ""
    key                  = "mlops.tfstate"
    workspace_key_prefix = ""
    region               = "us-west-2"
    dynamodb_table       = ""
    encrypt              = true
  }
}