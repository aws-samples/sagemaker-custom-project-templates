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

# Seed Code Checkin CodeBuild Project
output "seed_code_checkin_codebuild_project" {
  value = aws_codebuild_project.seed_code_checkin_build.id
}

# Model CodePipeline
output "model_codepipeline_id" {
  value = aws_codepipeline.model_pipeline.id
}
