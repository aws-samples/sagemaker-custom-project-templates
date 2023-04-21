
# SageMaker Model Object
resource "aws_sagemaker_model" "sm_model" {
  name               = "sagemaker-${var.sagemaker_project_name}-${var.endpoint_stage_name}"
  execution_role_arn = var.model_exec_role_arn

  container {
    image          = var.model_inference_image
    model_data_url = var.model_registry_artifact
  }
}


#SageMaker Endpoint Configuration
resource "aws_sagemaker_endpoint_configuration" "sm_endpoint_config" {
  depends_on = [aws_sagemaker_model.sm_model]
  name       = "sagemaker-${var.sagemaker_project_name}-${var.endpoint_stage_name}"

  production_variants {
    model_name             = aws_sagemaker_model.sm_model.name
    initial_instance_count = var.endpoint_instance_count
    instance_type          = var.endpoint_instance_type
    initial_variant_weight = 1
    variant_name           = "AllTraffic"
  }

  data_capture_config {
    enable_capture              = true
    initial_sampling_percentage = 80
    destination_s3_uri          = "s3://sagemaker-project-${var.sagemaker_project_id}/datacapture-${var.endpoint_stage_name}"

    capture_options {
      capture_mode = "Input"
    }
  }

}

#SageMaker Endpoint 
resource "aws_sagemaker_endpoint" "sm_endpoint" {
  depends_on           = [aws_sagemaker_endpoint_configuration.sm_endpoint_config]
  name                 = "sagemaker-${var.sagemaker_project_name}-${var.endpoint_stage_name}"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.sm_endpoint_config.name
}