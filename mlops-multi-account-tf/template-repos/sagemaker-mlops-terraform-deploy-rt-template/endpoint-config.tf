resource "aws_sagemaker_model" "model_rt_inference" {
  execution_role_arn = data.aws_ssm_parameter.sagemaker_role_arn.value
  vpc_config {
    security_group_ids = split(",", var.SGIds)
    subnets            = split(",", var.SubnetIds)

  }
  container {
    model_package_name = var.ModelPackageName
  }
  tags = {
    "sagemaker:project-name" = "${var.SageMakerProjectName}"
    "sagemaker:project-id"   = "${var.SageMakerProjectId}"
  }

} # Random_id is used to force the sagemaker endpoint to update.
# It is only regenerated it the model_name changes from the previous state.
# https://discuss.hashicorp.com/t/sagemaker-endpoint-not-updating-with-configuration-change/1727
resource "random_id" "force_endpoint_update" {
  keepers = {
    model_name = aws_sagemaker_model.model_rt_inference.name
  }

  byte_length = 8
}

resource "aws_sagemaker_endpoint_configuration" "sm_endpoint_configuration" {
  name = "${var.SageMakerProjectName}-endpoint-config-${random_id.force_endpoint_update.dec}"
  production_variants {
    variant_name           = "AllTraffic"
    model_name             = aws_sagemaker_model.model_rt_inference.name
    initial_instance_count = var.EndpointInstanceCount
    instance_type          = var.EndpointInstanceType
  }
  data_capture_config {
    enable_capture              = var.EnableDataCapture
    initial_sampling_percentage = var.SamplingPercentage
    destination_s3_uri          = "s3://${var.ProjectBucket}/${var.SageMakerProjectName}-${var.SageMakerProjectId}/datacapture"
    capture_options {
      capture_mode = "Input"
    }
    capture_content_type_header {
      csv_content_types = ["text/csv"]
    }
  }

  tags = {
    "sagemaker:project-name" = "${var.SageMakerProjectName}"
    "sagemaker:project-id"   = "${var.SageMakerProjectId}"
  }
  # By default Terraform destroys resources before creating the new one. However, in this case we want to force Terraform to create a
  # new resource first. If we do not enforce the order of: Create new endpoint config -> update sagemaker endpoint -> Destroy old endpoint config
  # Sagemaker will error when it tries to update from the old (destroyed) config to the new one.  This has no impact on runtime or uptime,
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_sagemaker_endpoint" "sm_endpoint" {
  name                 = "${var.SageMakerProjectName}-${var.Environment}"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.sm_endpoint_configuration.name
  tags = {
    "sagemaker:project-name" = "${var.SageMakerProjectName}"
    "sagemaker:project-id"   = "${var.SageMakerProjectId}"
  }
}


resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.SageMakerProjectName}-${var.SageMakerProjectId}-dashboard"

  dashboard_body = jsonencode(
    {
      "start" : "-PT9H",
      "periodOverride" : "inherit",
      "widgets" : [
        {
          "type" : "metric",
          "width" : 12,
          "height" : 6,
          "properties" : {
            "metrics" : [
              [
                "AWS/SageMaker",
                "InvocationsPerInstance",
                "EndpointName", "${aws_sagemaker_endpoint.sm_endpoint.name}",
                "VariantName", "AllTraffic"
              ],
              [
                "AWS/SageMaker",
                "Invocations",
                "EndpointName", "${aws_sagemaker_endpoint.sm_endpoint.name}",
                "VariantName", "AllTraffic"
              ]
            ],
            "period" : 60,
            "stat" : "Sum",
            "region" : "",
            "title" : "Number of invocations",
            "stacked" : false,
            "view" : "timeSeries",
            "liveData" : false
          }
        },

        {
          "type" : "metric",
          "width" : 12,
          "height" : 6,
          "properties" : {
            "metrics" : [
              [
                "AWS/SageMaker",
                "Invocation4XXErrors",
                "EndpointName", "${aws_sagemaker_endpoint.sm_endpoint.name}",
                "VariantName", "AllTraffic"
              ],
              [
                "AWS/SageMaker",
                "Invocation5XXErrors",
                "EndpointName", "${aws_sagemaker_endpoint.sm_endpoint.name}",
                "VariantName", "AllTraffic"
              ]
            ],
            "period" : 60,
            "stat" : "Sum",
            "region" : "${local.aws_region}",
            "title" : "Number of errors",
            "stacked" : false,
            "view" : "timeSeries",
            "liveData" : false
          }
        },

        {
          "type" : "metric",
          "width" : 12,
          "height" : 6,
          "properties" : {
            "metrics" : [
              [
                "AWS/SageMaker",
                "ModelLatency",
                "EndpointName", "${aws_sagemaker_endpoint.sm_endpoint.name}",
                "VariantName", "AllTraffic"
              ],
              [
                "AWS/SageMaker",
                "OverheadLatency",
                "EndpointName", "${aws_sagemaker_endpoint.sm_endpoint.name}",
                "VariantName", "AllTraffic"
              ]
            ],
            "period" : 60,
            "stat" : "Average",
            "region" : "${local.aws_region}",
            "title" : "Latency",
            "stacked" : false,
            "view" : "timeSeries",
            "liveData" : false
          }
        }
      ]
  })
}
