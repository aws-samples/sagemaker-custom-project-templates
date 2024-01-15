# This template is built and deployed by the infrastructure pipeline in various stages (pre-production/production) as required for Batch inference.
# It specifies the resources that need to be created, like the SageMaker Model. It can be extended to include resources as required.

resource "random_id" "force_sagemaker_pipeline_update" {

  byte_length = 8
}


resource "aws_sagemaker_pipeline" "BatchDeployPipeline" {
  pipeline_name         = "${var.BatchPipeline}-${random_id.force_sagemaker_pipeline_update.dec}"
  pipeline_display_name = var.BatchPipeline
  pipeline_description  = "The SM Pipeline that executes the batch inference"
  role_arn              = data.aws_ssm_parameter.sagemaker_role_arn.value
  pipeline_definition_s3_location {
    bucket     = var.ProjectBucket
    object_key = var.PipelineDefinitionS3Key
  }
  tags = {
    "sagemaker:project-name" = "${var.SageMakerProjectName}"
    "sagemaker:project-id"   = "${var.SageMakerProjectId}"
  }
}

resource "aws_sagemaker_model" "model" {
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

}
resource "aws_cloudwatch_event_rule" "sagemaker_pipeline_event_rule" {
  name                = "${var.SageMakerProjectName}-${var.Environment}-SchedExecRule"
  description         = "Trigger sagemaker pipeline"
  schedule_expression = "rate(${var.ScheduleExpressionforPipeline})"
}

resource "aws_cloudwatch_event_target" "sagemaker_pipeline_event_target" {
  arn      = aws_sagemaker_pipeline.BatchDeployPipeline.arn
  rule     = aws_cloudwatch_event_rule.sagemaker_pipeline_event_rule.name
  role_arn = data.aws_ssm_parameter.sagemaker_role_arn.value
  sagemaker_pipeline_target {
    pipeline_parameter_list {
      name  = "ProcessingInstanceCount"
      value = var.ProcessingInstanceCount
    }
    pipeline_parameter_list {
      name  = "ProcessingInstanceType"
      value = var.ProcessingInstanceType
    }
    pipeline_parameter_list {
      name  = "InferenceInstanceType"
      value = var.InferenceInstanceType
    }
    pipeline_parameter_list {
      name  = "InferenceInstanceCount"
      value = var.InferenceInstanceCount
    }

  }
}

resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.SageMakerProjectName}-${var.SageMakerProjectId}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        "type" : "metric",
        "x" : 0,
        "y" : 0,
        "width" : 12,
        "height" : 3,
        "properties" : {
          "metrics" : [
            ["AWS/Sagemaker/ModelBuildingPipeline", "ExecutionSucceeded", "PipelineName", "${aws_sagemaker_pipeline.BatchDeployPipeline.id}"],
            [".", "ExecutionFailed", ".", "."]
          ],
          "view" : "singleValue",
          "stacked" : false,
          "region" : "${local.aws_region}",
          "stat" : "Sum",
          "period" : 604800,
          "setPeriodToTimeRange" : true,
          "title" : "Number of Successful and Failed Runs"
        }
      },
      {
        "type" : "metric",
        "x" : 12,
        "y" : 0,
        "width" : 12,
        "height" : 3,
        "properties" : {
          "metrics" : [
            [{ "expression" : "m1/60000", "label" : "Average Duration Minute", "id" : "e1" }],
            ["AWS/Sagemaker/ModelBuildingPipeline", "ExecutionDuration", "PipelineName", "${aws_sagemaker_pipeline.BatchDeployPipeline.id}", { "id" : "m1", "visible" : false }]
          ],
          "view" : "singleValue",
          "stacked" : false,
          "region" : "${local.aws_region}",
          "stat" : "Average",
          "period" : 604800,
          "title" : "Pipeline Average Duration"
        }
      },
      {
        "type" : "metric",
        "x" : 0,
        "y" : 3,
        "width" : 12,
        "height" : 3,
        "properties" : {
          "metrics" : [
            ["AWS/Events", "Invocations", "RuleName", "${var.SageMakerProjectName}-${var.Environment}-SchedExecRule"],
            [".", "FailedInvocations", ".", "."]
          ],
          "view" : "singleValue",
          "stacked" : false,
          "region" : "${local.aws_region}",
          "stat" : "SampleCount",
          "period" : 604800,
          "title" : "Pipeline Triggers"
        }
      }
  ] })
}
