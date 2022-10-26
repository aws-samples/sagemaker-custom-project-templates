#----------------------------------------------------------------------------#
# This terraform component will create AWS CodePipeline for building the model
#----------------------------------------------------------------------------#

resource "aws_codepipeline" "model_pipeline" {
  name     = local.cmn_res_name
  role_arn = "arn:aws:iam::${local.account_id}:${var.sagemaker_service_catalog_codepipeline_role}"

  artifact_store {
    location = aws_s3_bucket.terraform_data_source_s3.id
    type     = "S3"
  }

  stage {
    name = "Source"

    action {
      name             = "ModelBuildWorkflowCode"
      category         = "Source"
      owner            = "AWS"
      provider         = "CodeStarSourceConnection"
      version          = "1"
      output_artifacts = ["ModelBuildSourceArtifact"]

      configuration = {
        ConnectionArn    = var.codestar_connection_arn
        FullRepositoryId = var.git_repo_name
        BranchName       = var.git_repo_branch
      }
    }
  }

  stage {
    name = "Build"

    action {
      name             = "BuildAndExecuteSageMakerPipeline"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      input_artifacts  = ["ModelBuildSourceArtifact"]
      output_artifacts = ["ModelBuildBuildArtifact"]
      version          = "1"

      configuration = {
        ProjectName = aws_codebuild_project.model_pipeline_build.id
      }
    }
  }

}