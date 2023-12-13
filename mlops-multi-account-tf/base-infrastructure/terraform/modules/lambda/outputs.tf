output "lambda_arn" {
  description = "The arn of the Lambda function"
  value       = aws_lambda_function.lambda.arn
}

output "lambda_name" {
  description = "The name of the Lambda function"
  value       = aws_lambda_function.lambda.function_name
}

output "log_name" {
  description = "The Cloudwatch log group name"
  value       = aws_cloudwatch_log_group.log_group.name
}

output "log_arn" {
  description = "The Cloudwatch log group arn"
  value       = aws_cloudwatch_log_group.log_group.arn

}
