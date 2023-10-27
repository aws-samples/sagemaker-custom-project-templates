resource "aws_lambda_layer_version" "pygithub_lambda_layer" {
  filename            = "./lambdas/layers/python_github_layer.zip"
  layer_name          = "pygithub_lambda_layer"
  compatible_runtimes = ["python3.8"]
}

data "archive_file" "clone_repo_zip_code" {
  type        = "zip"
  source_dir  = "./lambdas/functions/clone_repo_lambda/"
  output_path = "lambdas/clone_repo_lambda.zip"
}

data "archive_file" "trigger_workflow_zip_code" {
  type        = "zip"
  source_dir  = "./lambdas/functions/trigger_workflow_lambda/"
  output_path = "lambdas/trigger_workflow_lambda.zip"
}

module "clone_repo_lambda" {
  source                         = "../modules/lambda"
  description                    = "Lambda function to clone the template repository"
  function_name                  = "${var.prefix}_clone_repo_lambda"
  filename                       = "lambdas/clone_repo_lambda.zip"
  role                           = aws_iam_role.service_catalog_lambda_iam_role.arn
  handler                        = "lambda_function.lambda_handler"
  timeout                        = 200
  runtime                        = "python3.8"
  source_code_hash               = data.archive_file.clone_repo_zip_code.output_base64sha256
  layers                         = [aws_lambda_layer_version.pygithub_lambda_layer.arn]
  reserved_concurrent_executions = 5
  variables = {
    GITACCESSTOKEN = "sagemaker/github_pat",
    REGION         = local.aws_region
  }
  subnets_ids     = [module.networking.private_subnet_id]
  security_groups = [module.networking.sg_id]
}

module "trigger_workflow_lambda" {
  source                         = "../modules/lambda"
  description                    = "Lambda function to trigger a git actions workflow"
  function_name                  = "${var.prefix}_trigger_workflow_lambda"
  filename                       = "lambdas/trigger_workflow_lambda.zip"
  role                           = aws_iam_role.service_catalog_lambda_iam_role.arn
  handler                        = "lambda_function.lambda_handler"
  timeout                        = 200
  runtime                        = "python3.8"
  source_code_hash               = data.archive_file.trigger_workflow_zip_code.output_base64sha256
  layers                         = [aws_lambda_layer_version.pygithub_lambda_layer.arn]
  reserved_concurrent_executions = 5
  variables = {
    GITACCESSTOKEN = "sagemaker/github_pat",
    REGION         = local.aws_region
  }
  subnets_ids     = [module.networking.private_subnet_id]
  security_groups = [module.networking.sg_id]
}
