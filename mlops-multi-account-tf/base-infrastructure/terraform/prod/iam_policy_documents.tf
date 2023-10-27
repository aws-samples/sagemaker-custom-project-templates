#IAM policy document
data "aws_iam_policy_document" "sagemaker_pass_role_policy" {
  statement {
    actions = [
      "iam:PassRole"
    ]
    resources = [
      "arn:aws:iam::${local.account_id}:role/*"
    ]
    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values = [
        "events.amazonaws.com",
        "lambda.amazonaws.com",
        "sagemaker.amazonaws.com",
        "apigateway.amazonaws.com",
        "application-autoscaling.amazonaws.com"
      ]
    }
  }
}

data "aws_iam_policy_document" "deny_sagemaker_jobs_outside_vpc" {
  statement {
    effect = "Deny"
    actions = [
      "sagemaker:CreateModel",
      "sagemaker:CreateTrainingJob",
      "sagemaker:CreateProcessingJob"
    ]
    resources = [
      "*"
    ]
    condition {
      test     = "StringNotEquals"
      variable = "sagemaker:VpcSubnets"
      values   = [module.networking.private_subnet_id]
    }
  }
}

data "aws_iam_policy_document" "sagemaker_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type = "Service"
      identifiers = [
        "states.amazonaws.com",
        "events.amazonaws.com",
        "lambda.amazonaws.com",
        "sagemaker.amazonaws.com",
        "apigateway.amazonaws.com"
      ]
    }
  }
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type = "AWS"
      identifiers = [
        "arn:aws:iam::${local.account_id}:root"
      ]
    }
  }
}

data "aws_iam_policy_document" "sagemaker_projects_s3_policy" {
  statement {
    actions = [
      "s3:List*"
    ]
    resources = [
      "${module.sagemaker_projects_bucket.bucket_arn}/*",
      "${module.sagemaker_projects_bucket.bucket_arn}"
    ]
  }
  statement {
    actions = [
      "s3:GetObject",
      "s3:PutObject"
    ]
    resources = [
      "${module.sagemaker_projects_bucket.bucket_arn}/*"
    ]
  }
}

