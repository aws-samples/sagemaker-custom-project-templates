resource "aws_cloudwatch_event_rule" "event_rule" {
  name          = "${local.prefix}-${local.sm_project_name}-watch-for-model-approved"
    event_pattern = jsonencode({
    source : [
      "aws.sagemaker"
    ],
    "detail-type" : [
      "SageMaker Model Package State Change"
    ],
    "detail": {
      "ModelPackageGroupName": [ local.model_package_group_name ]
    }
  })
  description = "model package group state changed"
}

resource "aws_iam_role" "start_code_pipeline_role" {
  name               = "${local.prefix}-${local.sm_project_name}-start-codepipeline-role"
  assume_role_policy = data.aws_iam_policy_document.eventbridge_assume_policy.json
}

data "aws_iam_policy_document" "eventbridge_assume_policy" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "start_code_pipeline_role_policy" {
  statement {
    sid = ""
    actions = ["codepipeline:StartPipelineExecution"]
    resources = [
      aws_codepipeline.codepipeline.arn
    ]
    effect = "Allow"
  }
}

resource "aws_iam_role_policy" "start_code_pipeline_role" {
    role     = aws_iam_role.start_code_pipeline_role.id
    policy   = data.aws_iam_policy_document.start_code_pipeline_role_policy.json
}

resource "aws_cloudwatch_event_target" "target" {
  rule      = aws_cloudwatch_event_rule.event_rule.name
  target_id = aws_codepipeline.codepipeline.name
  arn       = aws_codepipeline.codepipeline.arn
  role_arn   = aws_iam_role.start_code_pipeline_role.arn
}
