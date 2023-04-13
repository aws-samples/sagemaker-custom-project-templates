# Variables
#------------
variable "sagemaker_project_name" {
  description = "SageMaker Project Name"
}

variable "sagemaker_project_id" {
  description = "SageMaker Project ID"
}

variable "model_exec_role_arn" {
  description = "AWS IAM ARN for the Model creation"
}


variable "model_registry_artifact" {
  description = "S3 URI having the model artifacts"
}

variable "model_inference_image" {
  description = "ECR Image for the Model Inference"
}

variable "endpoint_instance_count" {
  description = "Instance Count for Endpoint"
}


variable "endpoint_instance_type" {
  description = "Instance type for Endpoint"
}


variable "endpoint_stage_name" {
  description = "Stage Name to be used for Endpoint"
}
