provider "aws" {
  region = ""
}

terraform {
  required_version = ">= 1.0.0"
  backend "s3" {
    bucket = ""
    key    = "mlops-templates.tfstate"
    region = ""
  }
}


