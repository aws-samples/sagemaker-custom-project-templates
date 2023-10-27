variable "studio_domain_name" {
  type        = string
  description = "Name to assign to the SageMaker Studio domain"
  default     = "studio-domain"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID where to deploy SageMaker Studio"
}

variable "private_subnet_id" {
  type        = string
  description = "Private subnet id"
}

variable "private_subnet_id_2" {
  type        = string
  description = "Private subnet id"
}


variable "sg_id" {
  type        = string
  description = "Security group id"
}

variable "sm_studio_role_arn" {
  type        = string
  description = "SageMaker Studio ARN"
}

variable "data_scientist_execution_role_arn" {
  type        = string
  description = "Data Scientist role ARN"
}

variable "lead_data_scientist_execution_role_arn" {
  type        = string
  description = "Lead Data Scientist role ARN"
}
