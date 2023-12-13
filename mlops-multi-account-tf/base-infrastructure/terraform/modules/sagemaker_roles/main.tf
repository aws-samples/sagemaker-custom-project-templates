resource "aws_iam_policy" "sm_deny_policy" {
  name = "sm-deny-policy"
  policy = jsonencode(
    {
      Version = "2012-10-17"
      Statement = [
        {
          Action = [
            "sagemaker:CreateProject",
          ]
          Effect   = "Deny"
          Resource = "*"
        },
        {
          Action = [
            "sagemaker:UpdateModelPackage",
          ]
          Effect   = "Deny"
          Resource = "*"
        },
      ]
    }
  )
}

resource "aws_iam_policy" "services_policy" {
  name = "services-policy"
  policy = jsonencode(
    {
      Version = "2012-10-17"
      Statement = [
        {
          Action = [
            "lambda:Create*",
            "lambda:Update*",
            "lambda:Invoke*",
          ]
          Effect   = "Allow"
          Resource = "*"
        },
        {
          Action = [
            "sagemaker:ListTags",
          ]
          Effect   = "Allow"
          Resource = "*"
        },
        {
          Action = [
            "codecommit:GitPull",
            "codecommit:GitPush",
            "codecommit:*Branch*",
            "codecommit:*PullRequest*",
            "codecommit:*Commit*",
            "codecommit:GetDifferences",
            "codecommit:GetReferences",
            "codecommit:GetRepository",
            "codecommit:GetMerge*",
            "codecommit:Merge*",
            "codecommit:DescribeMergeConflicts",
            "codecommit:*Comment*",
            "codecommit:*File",
            "codecommit:GetFolder",
            "codecommit:GetBlob",
          ]
          Effect   = "Allow"
          Resource = "*"
        },
        {
          Action = [
            "ecr:BatchGetImage",
            "ecr:BatchCheckLayerAvailability",
            "ecr:GetDownloadUrlForLayer",
            "ecr:GetRepositoryPolicy",
            "ecr:DescribeRepositories",
            "ecr:DescribeImages",
            "ecr:ListImages",
            "ecr:GetAuthorizationToken",
            "ecr:GetLifecyclePolicy",
            "ecr:GetLifecyclePolicyPreview",
            "ecr:ListTagsForResource",
            "ecr:DescribeImageScanFindings",
            "ecr:CreateRepository",
            "ecr:CompleteLayerUpload",
            "ecr:UploadLayerPart",
            "ecr:InitiateLayerUpload",
            "ecr:PutImage",
          ]
          Effect   = "Allow"
          Resource = "*"
        },
        {
          Action = [
            "servicecatalog:*",
          ]
          Effect   = "Allow"
          Resource = "*"
        },
      ]
    }
  )
}

resource "aws_iam_policy" "kms_policy" {
  name = "kms-policy"
  policy = jsonencode(
    {
      Version = "2012-10-17"
      Statement = [
        {
          Action = [
            "kms:CreateGrant",
            "kms:Decrypt",
            "kms:DescribeKey",
            "kms:Encrypt",
            "kms:ReEncrypt",
            "kms:GenerateDataKey",
          ]
          Effect   = "Allow"
          Resource = "*"
        },
      ]
    }
  )
}

resource "aws_iam_policy" "s3_policy" {
  name = "s3-policy"
  policy = jsonencode(
    {
      Version = "2012-10-17"
      Statement = [
        {
          Action = [
            "s3:AbortMultipartUpload",
            "s3:DeleteObject",
            "s3:Describe*",
            "s3:GetObject",
            "s3:PutBucket*",
            "s3:PutObject",
            "s3:PutObjectAcl",
            "s3:GetBucketAcl",
            "s3:GetBucketLocation",
          ]
          Effect = "Allow"
          Resource = [
            "arn:aws:s3:::${var.s3_bucket_prefix}*/*",
            "arn:aws:s3:::${var.s3_bucket_prefix}*",
            "arn:aws:s3:::sagemaker*/*",
            "arn:aws:s3:::sagemaker*",
          ]
        },
        {
          Action = [
            "s3:ListBucket",
          ]
          Effect = "Allow"
          Resource = [
            "arn:aws:s3:::${var.s3_bucket_prefix}*",
            "arn:aws:s3:::sagemaker*",

          ]
        },
        {
          Action = [
            "s3:DeleteBucket*",
          ]
          Effect = "Deny"
          Resource = [
            "*"
          ]
        },
      ]
    }
  )
}

resource "aws_iam_role" "data_scientist_role" {
  name = "data_scientist_role"
  managed_policy_arns = [
    "${data.aws_iam_policy.AmazonSSMReadOnlyAccess.arn}",
    "${data.aws_iam_policy.AWSLambda_ReadOnlyAccess.arn}",
    "${data.aws_iam_policy.AWSCodeCommitReadOnly.arn}",
    "${data.aws_iam_policy.AmazonEC2ContainerRegistryReadOnly.arn}",
    "${data.aws_iam_policy.AmazonSageMakerFullAccess.arn}",
    aws_iam_policy.services_policy.arn,
    aws_iam_policy.kms_policy.arn,
    aws_iam_policy.s3_policy.arn,
    aws_iam_policy.sm_deny_policy.arn
  ]
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      },
      {
        Action = ["sts:AssumeRole", ]
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "sagemaker.amazonaws.com"
        }
      },
    ]
  })
}

resource "aws_iam_role" "lead_data_scientist_role" {
  name = "lead_data_scientist_role"
  managed_policy_arns = [
    "${data.aws_iam_policy.AmazonSSMReadOnlyAccess.arn}",
    "${data.aws_iam_policy.AWSLambda_ReadOnlyAccess.arn}",
    "${data.aws_iam_policy.AWSCodeCommitReadOnly.arn}",
    "${data.aws_iam_policy.AmazonEC2ContainerRegistryReadOnly.arn}",
    "${data.aws_iam_policy.AmazonSageMakerFullAccess.arn}",
    aws_iam_policy.services_policy.arn,
    aws_iam_policy.kms_policy.arn,
    aws_iam_policy.s3_policy.arn
  ]
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      },
      {
        Action = ["sts:AssumeRole", ]
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "sagemaker.amazonaws.com"
        }
      },
    ]
  })
}

resource "aws_iam_role" "sagemaker_studio_role" {
  name = "sagemaker_studio_role"
  managed_policy_arns = [
    "${data.aws_iam_policy.AmazonSSMReadOnlyAccess.arn}",
    "${data.aws_iam_policy.AWSLambda_ReadOnlyAccess.arn}",
    "${data.aws_iam_policy.AWSCodeCommitReadOnly.arn}",
    "${data.aws_iam_policy.AmazonEC2ContainerRegistryReadOnly.arn}",
    "${data.aws_iam_policy.AmazonSageMakerFullAccess.arn}",
    aws_iam_policy.services_policy.arn,
    aws_iam_policy.kms_policy.arn,
    aws_iam_policy.s3_policy.arn
  ]
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      },
      {
        Action = ["sts:AssumeRole", ]
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "sagemaker.amazonaws.com"
        }
      },
    ]
  })
}

