#################################
# Creates Lambda function
#################################

resource "aws_lambda_function" "lambda" {
  filename                       = var.filename
  description                    = var.description
  function_name                  = var.function_name
  role                           = var.role
  handler                        = var.handler
  timeout                        = var.timeout
  runtime                        = var.runtime
  layers                         = var.layers
  reserved_concurrent_executions = var.reserved_concurrent_executions
  source_code_hash               = var.source_code_hash
  tracing_config {
    mode = "Active"
  }
  environment {
    variables = var.variables
  }
  vpc_config {
    subnet_ids         = var.subnets_ids
    security_group_ids = var.security_groups
  }
}

#################################
# Create Cloudwatch group for the lambda
#################################
resource "aws_cloudwatch_log_group" "log_group" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = 365
}
