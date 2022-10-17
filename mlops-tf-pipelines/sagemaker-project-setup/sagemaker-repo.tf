#------------------------------------------------------------#
# Create AWS SageMaker repo from the ML Source Code repository
#------------------------------------------------------------#

resource "aws_sagemaker_code_repository" "sagemaker_model_build_repo" {
  code_repository_name = "sagemaker-${var.sagemaker_project_id}-modelbuild"

  git_config {
    repository_url = var.git_repo_url
    secret_arn     = var.secrets_manager_secret_arn
  }
}