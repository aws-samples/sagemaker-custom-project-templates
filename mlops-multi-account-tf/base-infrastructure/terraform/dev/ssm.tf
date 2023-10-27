#lambda parameters
resource "aws_ssm_parameter" "arn_clone_repo_lambda" {
  name        = "arn_clone_repo_lambda"
  description = "Arn lambda function clone repo from template repo"
  type        = "String"
  overwrite   = true
  value       = module.clone_repo_lambda.lambda_arn
}

resource "aws_ssm_parameter" "arn_trigger_workflow_lambda" {
  name        = "arn_trigger_workflow_lambda"
  description = "Arn lambda function trigger a workflow once a model is approved in model registry"
  type        = "String"
  overwrite   = true
  value       = module.trigger_workflow_lambda.lambda_arn
}

resource "aws_ssm_parameter" "name_trigger_workflow_lambda" {
  name        = "name_trigger_workflow_lambda"
  description = "Name lambda function trigger a workflow once a model is approved in model registry"
  type        = "String"
  overwrite   = true
  value       = module.trigger_workflow_lambda.lambda_name
}

#Github repo
resource "aws_ssm_parameter" "github_organization" {
  name        = "github_organization"
  description = "Name github organization"
  type        = "String"
  overwrite   = true
  value       = "sagemaker-mlops-terraform"
}

resource "aws_ssm_parameter" "github_build_repo_template" {
  name        = "github_build_repo_template"
  description = "Template repository name for building"
  type        = "String"
  overwrite   = true
  value       = "model-training"
}

resource "aws_ssm_parameter" "github_deploy_rt_repo_template" {
  name        = "github_deploy_rt_repo_template"
  description = "Template repository name for deploying Real time inference"
  type        = "String"
  overwrite   = true
  value       = "model-deployment-realtime"
}

resource "aws_ssm_parameter" "github_deploy_batch_repo_template" {
  name        = "github_deploy_batch_repo_template"
  description = "Template repository name for deploying inference in batch"
  type        = "String"
  overwrite   = true
  value       = "model-deployment-batch"

}

resource "aws_ssm_parameter" "github_byoc_repo_template" {
  name        = "github_container_repo_template"
  description = "Template repository name for deploying inference in batch"
  type        = "String"
  overwrite   = true
  value       = "container-build"
}

resource "aws_ssm_parameter" "github_workflow_repo_template" {
  name        = "github_workflow_repo_template"
  description = "Template repository name for workflow promotion"
  type        = "String"
  overwrite   = true
  value       = "pipeline-promotion"
}


#policies

resource "aws_ssm_parameter" "arn_sagemaker_pass_role_policy" {
  name      = "arn_sagemaker_pass_role_policy"
  type      = "String"
  overwrite = true
  value     = aws_iam_policy.sagemaker_pass_role_policy.arn
}

resource "aws_ssm_parameter" "arn_sagemaker_execution_policy" {
  name      = "arn_sagemaker_execution_policy"
  type      = "String"
  overwrite = true
  value     = aws_iam_policy.sagemaker_execution_policy.arn
}

resource "aws_ssm_parameter" "arn_sagemaker_related_policy" {
  name      = "arn_sagemaker_related_policy"
  type      = "String"
  overwrite = true
  value     = aws_iam_policy.sagemaker_related_policy.arn
}

resource "aws_ssm_parameter" "arn_sagemaker_s3_policy" {
  name      = "arn_sagemaker_s3_policy"
  type      = "String"
  overwrite = true
  value     = aws_iam_policy.sagemaker_s3_policy.arn
}

resource "aws_ssm_parameter" "arn_sagemaker_vpc_policy" {
  name      = "arn_sagemaker_vpc_policy"
  type      = "String"
  overwrite = true
  value     = aws_iam_policy.sagemaker_vpc_policy.arn
}
resource "aws_ssm_parameter" "arn_deny_sagemaker_jobs_outside_vpc" {
  name      = "arn_deny_sagemaker_jobs_outside_vpc"
  type      = "String"
  overwrite = true
  value     = aws_iam_policy.deny_sagemaker_jobs_outside_vpc.arn
}

#Deployment accounts

resource "aws_ssm_parameter" "preprod_account_number_ssm" {
  name      = "preprod_account_number"
  type      = "String"
  overwrite = true
  value     = var.preprod_account_number
}
resource "aws_ssm_parameter" "prod_account_number_ssm" {
  name      = "prod_account_number"
  type      = "String"
  overwrite = true
  value     = var.prod_account_number
}

# Secrets Manager for Github Personal Access Token
resource "aws_secretsmanager_secret" "github_pat" {
  name = "sagemaker/github_pat"
}

resource "aws_secretsmanager_secret_version" "github_pat_version" {
  secret_id     = aws_secretsmanager_secret.github_pat.id
  secret_string = jsonencode({ "github_pat" : "${var.pat_github}" })
}
