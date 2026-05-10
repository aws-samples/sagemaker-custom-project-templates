variable "prefix" {
  type        = string
  description = "Naming prefix to use for resources"
}

variable "kms_key_arn" {
  type        = string
  description = "Kms key arn for SM"
}
