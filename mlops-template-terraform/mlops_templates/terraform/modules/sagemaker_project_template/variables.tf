variable "template_name" {
  type        = string
  description = "Name of template, used to lookup seed_code and CloudFormation templates for service catalog"
}

variable "owner" {
  type        = string
  description = "Owner of the service catalog product"
}

variable "sagemaker_execution_role_arn" {
  type        = string
  description = "Sagemaker Execution Role ARN"
}

variable "template_key" {
  type        = string
  description = "S3 Key for storing service catalog template"
}

variable "template_local_path" {
  type        = string
  description = "Path to local service catalog product template file"
}

variable "seed_code_map" {
  type        = map(any)
  description = "Map of seed code for template"
}
variable "template_vars" {
  type        = map(any)
  description = "Values to substitute into service catalog product template"
}
