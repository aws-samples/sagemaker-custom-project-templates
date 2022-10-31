#--------------------------------------------------------#  
# Create AWS CodeBuild Project for GIT Seed Code Checkin
#--------------------------------------------------------#

resource "aws_codebuild_project" "seed_code_checkin_build" {
  name         = "${local.cmn_res_name}-seed-code-checkin"
  description  = "Checkin the initial seed code into the given repository"
  service_role = "arn:aws:iam::${local.account_id}:${var.sagemaker_service_catalog_codebuild_role}"

  artifacts {
    type = "NO_ARTIFACTS"
  }

  environment {
    compute_type = "BUILD_GENERAL1_SMALL"
    image        = "aws/codebuild/amazonlinux2-x86_64-standard:3.0"
    type         = "LINUX_CONTAINER"
  }

  source {
    type      = "S3"
    location  = var.seed_code_s3_location
    buildspec = "buildspec.yml"
  }
}