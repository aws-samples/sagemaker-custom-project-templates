variable "environment" {
  description = "Environment"
  type        = string
}
variable "region" {
  description = "AWS Region"
  type        = string
}
variable "preprod_account_number" {
  description = "Prepod account number"
  type        = string
}
variable "prod_account_number" {
  description = "Prod account number"
  type        = string
}
variable "s3_bucket_prefix" {
  description = "S3 bucket where data are stored"
  type        = string
}
variable "prefix" {
  description = "Lambda function name prefix for Lambda functions"
}
variable "pat_github" {
  description = "Github Personal access token"
  sensitive   = true
}

