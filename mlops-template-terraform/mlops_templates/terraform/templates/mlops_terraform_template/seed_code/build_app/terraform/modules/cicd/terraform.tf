terraform {
  required_version = ">= 1.0 , <= 1.2.4"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.0"
    }
  }
}
