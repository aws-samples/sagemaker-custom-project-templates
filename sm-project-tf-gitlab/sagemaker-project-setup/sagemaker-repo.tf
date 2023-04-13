#------------------------------------------------------------#
# Create AWS SageMaker repo from the ML Source Code repository
#------------------------------------------------------------#

resource "aws_sagemaker_code_repository" "sagemaker_model_build_repo" {
  depends_on           = [aws_lambda_invocation.seed_code_lambda_trigger]
  code_repository_name = "sagemaker-${var.sagemaker_project_id}-modelbuild"
  tags                 = { "sagemaker:project-name" : var.sagemaker_project_name, "sagemaker:project-id" : var.sagemaker_project_id }

  git_config {
    repository_url = "${var.gitlab_url}/${var.git_user_name}/${var.git_build_repo_name}.git"
    secret_arn     = var.secrets_manager_gitlab_user_secret_arn
  }

}

resource "aws_sagemaker_code_repository" "sagemaker_model_deploy_repo" {
  depends_on           = [aws_lambda_invocation.seed_code_lambda_trigger]
  code_repository_name = "sagemaker-${var.sagemaker_project_id}-modeldeploy"
  tags                 = { "sagemaker:project-name" : var.sagemaker_project_name, "sagemaker:project-id" : var.sagemaker_project_id }

  git_config {
    repository_url = "${var.gitlab_url}/${var.git_user_name}/${var.git_deploy_repo_name}.git"
    secret_arn     = var.secrets_manager_gitlab_user_secret_arn
  }

}