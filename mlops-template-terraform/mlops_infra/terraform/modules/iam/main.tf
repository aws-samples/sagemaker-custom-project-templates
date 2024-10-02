# TODO: Consider scoping down IAM roles depending on your needs

locals {
  prefix         = var.prefix
  sm_execution_role_name = "${local.prefix}-sagemaker-execution-role"
  kms_key_arn            = var.kms_key_arn
}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}
##################################################################################################
# Roles & Policies
##################################################################################################

resource "aws_iam_role" "sagemaker_execution_role" {
  name = local.sm_execution_role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = "AllowRoleAssume"
        Principal = {
          Service = "sagemaker.amazonaws.com"
        }
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "aws_sagemaker_full_access" {
  role       = aws_iam_role.sagemaker_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

resource "aws_iam_role_policy_attachment" "aws_sagemaker_cloudformation_poweruser" {
  role       = aws_iam_role.sagemaker_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/AWSCloudFormationFullAccess"
}


resource "aws_iam_policy" "codecommit_policy" {
  name        = "${local.prefix}-codecommit-policy"
  description = "${local.prefix} policy for SM Studio codecommit access"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "codecommit:*"
      ],
      "Effect": "Allow",
      "Resource": "arn:aws:codecommit:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:${local.prefix}*"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "attach_codecommit_policy" {
  role       = aws_iam_role.sagemaker_execution_role.name
  policy_arn = aws_iam_policy.codecommit_policy.arn
}

resource "aws_iam_policy" "codebuild_policy" {
  name        = "${local.prefix}-codebuild-policy"
  description = "codebuild_policy for SM Studio"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "codebuild:*"
      ],
      "Effect": "Allow",
      "Resource": [
        "arn:aws:codebuild:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:project/${local.prefix}*"
        ]
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "attach_codebuild_policy" {
  role       = aws_iam_role.sagemaker_execution_role.name
  policy_arn = aws_iam_policy.codebuild_policy.arn
}

resource "aws_iam_policy" "codepipeline_policy" {
  name        = "${local.prefix}-codepipeline-policy"
  description = "codepipeline_policy for SM Studio"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "codepipeline:*"
      ],
      "Effect": "Allow",
      "Resource": "arn:aws:codepipeline:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:${local.prefix}*"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "attach_codepipeline_policy" {
  role       = aws_iam_role.sagemaker_execution_role.name
  policy_arn = aws_iam_policy.codepipeline_policy.arn
}


resource "aws_iam_role_policy_attachment" "aws_sagemaker_s3_full_access" {
  role       = aws_iam_role.sagemaker_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_policy" "eventbridge_policy" {
  name        = "${local.prefix}-eventbridge-policy"
  description = "EventBridge Policy for SM Execution Role"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "events:*"
      ],
      "Effect": "Allow",
      "Resource": "arn:aws:events:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:rule/${local.prefix}*"
    }
  ]
}
EOF
}


resource "aws_iam_role_policy_attachment" "attach_eventbridge_policy" {
  role       = aws_iam_role.sagemaker_execution_role.name
  policy_arn = aws_iam_policy.eventbridge_policy.arn
}

resource "aws_iam_policy" "kms_policy" {
  name        = "${local.prefix}-kms-policy"
  description = "kms_policy for SM Studio"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "kms:*"
      ],
      "Effect": "Allow",
      "Resource": "${local.kms_key_arn}"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "attach_kms_gran_policy" {
  role       = aws_iam_role.sagemaker_execution_role.name
  policy_arn = aws_iam_policy.kms_policy.arn
}

resource "aws_iam_policy" "iam_create_role" {
  name        = "${local.prefix}-iam-policy"
  description = "iam_create_role_policy for SM Studio"

  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "RoleActions",
            "Effect": "Allow",
            "Action": [
                "iam:CreateRole",
                "iam:GetRole",
                "iam:ListRolePolicies",
                "iam:ListAttachedRolePolicies",
                "iam:ListInstanceProfilesForRole",
                "iam:DeleteRole",
                "iam:PutRolePolicy",
                "iam:GetRolePolicy",
                "iam:DeleteRolePolicy",
                "iam:AttachRolePolicy"
            ],
            "Resource":  "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${local.prefix}*"
        },
        {
            "Sid": "PolicyActions",
            "Effect": "Allow",
            "Action": [
                "iam:CreatePolicy",
                "iam:GetPolicy",
                "iam:ListRolePolicies",
                "iam:ListAttachedRolePolicies",
                "iam:PutRolePolicy",
                "iam:GetRolePolicy",
                "iam:DeleteRolePolicy",
                "iam:AttachRolePolicy",
                "iam:DetachRolePolicy"
            ],
            "Resource":  [
              "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/${local.prefix}*"
            ]
        },
        {
            "Sid": "DetachManagedPolicies",
            "Effect": "Allow",
            "Action": [
                "iam:DeleteRolePolicy",
                "iam:DetachRolePolicy"
            ],
            "Resource":  [
              "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${local.prefix}*"
            ]
        },
        {
            "Sid": "PassRoleToSMPipelines",
            "Effect": "Allow",
            "Action": [
                "iam:PassRole"
            ],
            "Resource": [
              "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${local.prefix}*"
            ]
        },
        {
            "Sid": "TerraformAccessPolicies",
            "Effect": "Allow",
            "Action": [
                "iam:CreatePolicy",
                "iam:GetPolicy",
                "iam:GetPolicyVersion",
                "iam:ListPolicyVersions",
                "iam:CreatePolicyVersion",
                "iam:DeletePolicy",
                "iam:DeletePolicyVersion"
            ],
            "Resource": [
              "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/terraform-*"
            ]
        }
    ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "iam_create_role_attach" {
  role       = aws_iam_role.sagemaker_execution_role.name
  policy_arn = aws_iam_policy.iam_create_role.arn
}