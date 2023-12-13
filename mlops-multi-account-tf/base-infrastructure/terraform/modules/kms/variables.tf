variable "description" {
  type        = string
  description = "Description of KMS key"
  default     = "KMS Key for Machine Learning workloads."
}

# Cross Account Read
variable "trusted_accounts_for_decrypt_access" {
  description = "List of AWS account numbers that read ML artifacts from the bucket"
  type        = list(string)
  default     = []
}

variable "account_id" {
  description = "AWS account ID"
  type        = string
}
