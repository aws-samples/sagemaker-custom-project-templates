#------------------------------------------------#
# Terraform Main Component
# Has the following block definitions:
# - AWS Provider
# - Data Source for AWS Caller Identity
# - Important Outputs of this Terraform execution
#------------------------------------------------#

#AWS Provider
provider "aws" {}


#Data Source for Caller Identity
data "aws_caller_identity" "current" {}


#Important Outputs

#Command Runner IAM Exec Role Instance Profile
output "command_runner_instance_profile" {
  value = aws_iam_instance_profile.c_runner_instance_profile.name
}

#S3 Bucket Name
output "s3_bucket_id" {
  value = aws_s3_bucket.terraform_data_source_s3.id
}

#Secrets Manager Secret Name
output "secrets_manager_github_secret_arn" {
  value = aws_secretsmanager_secret.git_repo_secret.arn
}
