data "aws_caller_identity" "current" {}

locals {
  prefix = var.prefix
  model_name                            = var.model_name
  initial_instance_count                = var.initial_instance_count
  instance_type                         = var.instance_type
  sagemaker_endpoint_name               = var.sagemaker_endpoint_name
  variant_name                          = var.variant_name
  sagemaker_execution_role              = var.sagemaker_execution_role
  inference_image                       = var.inference_image
  model_data_url                        = var.model_data_url
}


resource "random_id" "force_endpoint_update" {
    keepers = {
      # Generate a new id each time we switch model data url
      model_data_url = local.model_data_url
  }
  byte_length = 8
}

resource "aws_sagemaker_model" "model" {
  name               = "${local.prefix}-${local.model_name}-${random_id.force_endpoint_update.dec}"
  execution_role_arn = local.sagemaker_execution_role

  container {
    image          = local.inference_image
    model_data_url = local.model_data_url
  }
}

resource "aws_sagemaker_endpoint_configuration" "inference_endpoint_configuration" {
  name        = "${local.sagemaker_endpoint_name}-${random_id.force_endpoint_update.dec}"

  production_variants {
    variant_name           = local.variant_name
    model_name             = aws_sagemaker_model.model.name
    initial_instance_count = local.initial_instance_count
    instance_type          = local.instance_type
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_sagemaker_endpoint" "inference_endpoint" {
  endpoint_config_name = aws_sagemaker_endpoint_configuration.inference_endpoint_configuration.name
  name                 = local.sagemaker_endpoint_name
}