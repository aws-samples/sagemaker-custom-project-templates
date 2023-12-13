variable "s3_bucket_name" {
  description = "The name of the bucket"
  type        = string
}

variable "s3_bucket_force_destroy" {
  description = "String Boolean to set bucket to be undeletable (well more difficult anyway) e.g: true/false"
  type        = string
}

variable "mfa_delete" {
  type        = string
  description = "To enable/disable MFA delete"
  default     = "Disabled"
}

variable "versioning" {
  type        = string
  description = "To enable/disable Versioning"
  default     = "Disabled"
}

variable "sse_algorithm" {
  description = "The type of encryption algorithm to use"
  type        = string
  default     = "aws:kms"
}

variable "s3_bucket_policy" {}

variable "kms_key_id" {
  type    = string
  default = ""
}


variable "cfn_file_name" {
  type        = string
  default     = ""
  description = "The name of s3 key."
}

variable "object_source" {
  type        = string
  default     = ""
  description = "The location of objects to be added to s3 "
}

# Life Cycle Config
variable "days_to_intellegent_tiering" {
  description = "Number of days to transition object to INTELLEGENT_TIERING."
  type        = number
  default     = 30
}

variable "non_current_days_to_standard_ia" {
  description = "Number of days to transition NON CURRENT object to STANDARD_IA."
  type        = number
  default     = 30
}

variable "non_current_days_to_glacier" {
  description = "Number of days to transition NON CURRENT object to GLACIER."
  type        = number
  default     = 90
}

variable "non_current_days_to_expire" {
  description = "Number of days to expire NON CURRENT objects."
  type        = number
  default     = 360
}
variable "abort_incomplete_upload" {
  description = "Number of days until abort incomplete upload"
  type        = number
  default     = 1
}
