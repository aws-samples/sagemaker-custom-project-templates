
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  aws_region = data.aws_region.current.name
}

variable "BatchPipeline" {
  description = "Name Sagemaker pipeline"
  type        = string
}

variable "ProjectBucket" {
  description = "S3 bucket sagemaker project"
  type        = string
}

variable "PipelineDefinitionS3Key" {
  description = "S3 bucket key where the pipeline definition is stored"
  type        = string
}
variable "SageMakerProjectName" {
  description = "SageMaker project name"
  type        = string
}

variable "SageMakerProjectId" {
  description = "SageMaker project id"
  type        = string
}

variable "Environment" {
  description = "Environment where is deployed"
  type        = string
}

variable "ScheduleExpressionforPipeline" {
  description = "The rate of execution of your pipeline (default 1 day)"
  type        = string
  default     = "1 day"
}

variable "ProcessingInstanceCount" {
  description = "The number of instance used for preprocessing step"
  type        = string
}

variable "ProcessingInstanceType" {
  description = "The type of instance used for preprocessing"
  type        = string
}

variable "InferenceInstanceCount" {
  description = "The number of instance used for inference step"
  type        = string
}

variable "InferenceInstanceType" {
  description = "The type of instance used for inference"
  type        = string
}

variable "MseThreshold" {
  description = "Maximun MSE allowed for create the model"
  type        = string
}

variable "InputDataUrl" {
  description = "Url for data for train the model"
  type        = string
}

variable "BatchDataUrl" {
  description = "Url for data for batch inference"
  type        = string
}

variable "TrainingInstanceCount" {
  description = "The number of instance used for training step"
  type        = string
}


data "aws_ssm_parameter" "sagemaker_role_arn" {
  name = "/${var.Environment}/sagemaker_role_arn"
}

variable "region" {
  description = "AWS Region"
  type        = string
}
