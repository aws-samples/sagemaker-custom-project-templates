# Copyright (c) HashiCorp, Inc.
# SPDX-License-Identifier: MPL-2.0

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "4.63.0"
    }

    random = {
      source  = "hashicorp/random"
      version = "3.5.1"
    }
  }
}

provider "aws" {}

resource "random_string" "random" {
  length  = var.random_string_length
  special = false
  upper   = false
}

resource "aws_s3_bucket" "my-bucket" {
  bucket = "mlops-tf-cloud-demo-${random_string.random.result}"
}

variable "random_string_length" {
  type        = number
  description = "Length of the random string to append to the bucket name"
  default     = 16
}

output "bucket_name" {
  value = aws_s3_bucket.my-bucket.bucket
}

