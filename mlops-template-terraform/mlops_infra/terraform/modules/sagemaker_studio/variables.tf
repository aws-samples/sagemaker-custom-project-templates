variable "domain_name" {
  type        = string
  description = "SageMaker Studio Domain Name"
}

variable "auth_mode" {
  type        = string
  description = "SageMaker Studio Domain Auth Mode"
  default     = "IAM"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID to deploy studio domain into"
}


variable "subnet_ids" {
  type        = list(string)
  description = "Subnets to deploy Studio into"
}

variable "sm_execution_role_arn" {
  type        = string
  description = "Sagemaker Execution Role ARN"
}

variable "kms_key_arn" {
  type        = string
  description = "KMS Key ARN"
}

variable "user_profile_names" {
  type        = list(string)
  description = "Studio User Names"
  default     = ["default_user"]
}

variable "jupyter_app_name" {
  type        = string
  description = "Jupyter App Name"
  default     = "ml-dev"
}

