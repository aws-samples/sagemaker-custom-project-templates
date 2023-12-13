variable "environment" {
  type        = string
  description = "Environment"
}
variable "bucket_id" {
  type        = string
  description = "Bucket ID with Sagemaker Templates"
}
variable "bucket_domain_name" {
  type        = string
  description = "The AWS region this bucket resides in"
}
variable "lead_data_scientist_execution_role_arn" {
  type        = string
  description = "Lead Data Scientist role ARN"
}
variable "launch_role" {
  type        = string
  description = "Launch Role ARN"
}
variable "templates" {
  type = map(object({
    name        = string
    file        = string
    description = string
  }))
  description = "List of template files"
}
