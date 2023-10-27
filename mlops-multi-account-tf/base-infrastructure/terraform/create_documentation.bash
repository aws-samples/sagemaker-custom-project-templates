#!/bin/bash

terraform-docs -c .terraform-docs.yml modules/kms
terraform-docs -c .terraform-docs.yml modules/lambda
terraform-docs -c .terraform-docs.yml modules/networking
terraform-docs -c .terraform-docs.yml modules/s3
terraform-docs -c .terraform-docs.yml modules/sagemaker
terraform-docs -c .terraform-docs.yml modules/sagemaker_roles
terraform-docs -c .terraform-docs.yml dev/
terraform-docs -c .terraform-docs.yml preprod/
terraform-docs -c .terraform-docs.yml prod/

