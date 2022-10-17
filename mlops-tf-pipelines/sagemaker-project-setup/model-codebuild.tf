#------------------------------------------------#
# This terraform component will create AWS CodeBuild Project for Building Model
#------------------------------------------------#

resource "aws_codebuild_project" "model_pipeline_build" {
  name         = local.cmn_res_name
  description  = "Builds the model building workflow code repository, creates the dSageMaker Pipeline and executes it"
  service_role = "arn:aws:iam::${local.account_id}:${var.sagemaker_service_catalog_codebuild_role}"

  artifacts {
    type = "CODEPIPELINE"
  }

  environment {
    compute_type = "BUILD_GENERAL1_SMALL"
    image        = "aws/codebuild/amazonlinux2-x86_64-standard:3.0"
    type         = "LINUX_CONTAINER"

    environment_variable {
      name  = "SAGEMAKER_PROJECT_NAME"
      value = var.sagemaker_project_name
    }
    environment_variable {
      name  = "SAGEMAKER_PROJECT_ID"
      value = var.sagemaker_project_id
    }

    environment_variable {
      name  = "ARTIFACT_BUCKET"
      value = aws_s3_bucket.terraform_data_source_s3.id
    }

    environment_variable {
      name  = "SAGEMAKER_PIPELINE_NAME"
      value = "sagemaker-${var.sagemaker_project_name}"
    }

    environment_variable {
      name  = "SAGEMAKER_PIPELINE_ROLE_ARN"
      value = "arn:aws:iam::${local.account_id}:${var.sagemaker_service_catalog_exec_role}"
    }

    environment_variable {
      name  = "AWS_REGION"
      value = var.region
    }

    environment_variable {
      name  = "SAGEMAKER_PROJECT_ARN"
      value = "arn:aws:sagemaker:${var.region}:${local.account_id}:${var.sagemaker_project_name}"
    }
  }

  source {
    type      = "CODEPIPELINE"
    buildspec = "codebuild-buildspec.yml"
  }
}


