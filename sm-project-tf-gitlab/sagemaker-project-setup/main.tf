#------------------------------------------------#
# Terraform Main Component
# Has the following block definitions:
# - AWS Provider
# - Data Source for AWS Caller Identity
# - Important Outputs of this Terraform execution
#------------------------------------------------#

#AWS Provider
provider "aws" {}



# Data Source for Caller Identity
data "aws_caller_identity" "current" {}


# Important Outputs

# S3 Bucket Name
output "s3_bucket_id" {
  value = aws_s3_bucket.terraform_data_source_s3.id
}
