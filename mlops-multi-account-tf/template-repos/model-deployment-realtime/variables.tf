
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  aws_region = data.aws_region.current.name
}

data "aws_ssm_parameter" "sagemaker_role_arn" {
  name = "/${var.Environment}/sagemaker_role_arn"
}

variable "region" {
  description = "AWS Region"
  type        = string
}

variable "Environment" {
  description = "Environment where is deployed"
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


variable "SubnetIds" {
  description = "List private subents"
}

variable "SGIds" {
  description = "List security groups"
}

variable "ModelPackageName" {
  description = "ARN model to deploy"
  type        = string
}

variable "EndpointInstanceCount" {
  description = "Number of instances to launch for the endpoint."
  type        = string
}

variable "EndpointInstanceType" {
  description = "The ML compute instance type for the endpoint."
  type        = string
}

variable "ProjectBucket" {
  description = "S3 bucket sagemaker project"
  type        = string
}

variable "EnableDataCapture" {
  description = "Enable Data capture"
  type        = string
  default     = "true"
}

variable "SamplingPercentage" {
  description = "The sampling percentage"
  type        = number
}
