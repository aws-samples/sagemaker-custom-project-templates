#S3 bucket for storing ML models
resource "aws_ssm_parameter" "s3_artifacts_buckets" {
  name        = "/${var.environment}/sagemaker_ml_artifacts_s3_bucket"
  description = "S3 ml artifacts"
  type        = "String"
  overwrite   = true
  value       = module.sagemaker_projects_bucket.bucket_id
}

#Role for executing Sagemaker deployment
resource "aws_ssm_parameter" "sagemaker_role_arn" {
  name        = "/${var.environment}/sagemaker_role_arn"
  description = "Role for SM deployments"
  type        = "String"
  overwrite   = true
  value       = aws_iam_role.sagemaker_execution_role.arn
}
