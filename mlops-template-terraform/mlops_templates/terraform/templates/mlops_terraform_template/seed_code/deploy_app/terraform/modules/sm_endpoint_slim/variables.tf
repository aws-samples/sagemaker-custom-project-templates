variable "prefix" {
  type        = string
  description = "Namespace prefix from the template."
}

variable "initial_instance_count" {
  default     = 1
  description = "Instance Count."
  type        = number
}

variable "instance_type" {
  default     = "ml.t2.medium"
  description = "Instance Type."
  type        = string
}

variable "model_name" {
  description = "Model Name."
  type        = string
}

variable "sagemaker_endpoint_name" {
  description = "The name of the sagemaker endpoint."
  type        = string
}

variable "variant_name" {
  default     = "variant-1"
  description = "The name of the variant."
  type        = string
}

variable "sagemaker_execution_role" {
  description = "The name of the SM execution role for the model"
  type        = string
}

variable "inference_image" {
  type        = string
  description = "SageMaker inference image"
}

variable "model_data_url" {
  type        = string
  description = "SageMaker model data url"
}
