# Copyright (c) HashiCorp, Inc.
# SPDX-License-Identifier: MPL-2.0

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.12.0"
    }
  }
}

data "aws_caller_identity" "current" {}

resource "random_string" "random" {
  length  = 16
  special = false
  lower   = true
  upper   = false
}

# # # #
# THE PROVISIONING ARTIFACT (TERRAFORM CONFIGURATION FILES)

resource "aws_s3_bucket" "artifact_bucket" {
  bucket = "mlops-tf-cloud-artifact-${random_string.random.result}"
}

resource "aws_s3_object" "artifact" {
  bucket = aws_s3_bucket.artifact_bucket.id
  key    = "product.tar.gz"
  source = "${path.module}/product.tar.gz"
  etag   = filemd5("${path.module}/product.tar.gz")
}

# # # #
# THE PRODUCT IN SERVICE CATALOG
resource "aws_servicecatalog_product" "example" {
  name        = "mlops-tf-cloud-example"
  description = "Automate the model building workflow. Process data, extract features, train and test models, and register them in the model registry. The template provisions an AWS CodeCommit repository for checking in and managing code versions. You can customize the seed code and the configuration files to suit your requirements. Model building pipeline: SageMaker Pipelines Coderepository: AWS CodeCommit Orchestration: AWS CodePipeline"
  owner       = var.service_catalog_product_owner
  type        = "TERRAFORM_CLOUD"
  tags = {
    # NOTE: This tag is read by SageMaker Studio to determine if the product should be visible in the SageMaker Studio UI.
    "sagemaker:studio-visibility" = "true"
  }

  provisioning_artifact_parameters {
    disable_template_validation = true
    template_url                = "https://s3.amazonaws.com/${aws_s3_object.artifact.bucket}/${aws_s3_object.artifact.key}"
    type                        = "TERRAFORM_CLOUD"
  }
}

locals {
  _product_name_convert_snake_case_to_class_case = join("", [for word in split("_", aws_servicecatalog_product.example.name) : title(word)])
  _product_name_convert_kebab_case_to_class_case = join("", [for word in split("-", local._product_name_convert_snake_case_to_class_case) : title(word)])
  class_case_product_name                        = local._product_name_convert_kebab_case_to_class_case
  unique_portfolio_ids                           = { for index, portfolio_id in var.service_catalog_portfolio_ids : index => portfolio_id }
  portfolio_role_pairs = [
    for portfolio in local.unique_portfolio_ids : [
      for role_arn in var.sagemaker_user_role_arns : {
        portfolio_id = portfolio
        role_arn     = role_arn
      }
    ]
  ]
  flattened_portfolio_role_pairs = flatten(local.portfolio_role_pairs)
}

resource "aws_servicecatalog_tag_option_resource_association" "example_product_managed_by" {
  resource_id   = aws_servicecatalog_product.example.id
  tag_option_id = aws_servicecatalog_tag_option.product_managed_by.id
}

resource "aws_servicecatalog_tag_option" "product_managed_by" {
  key   = "ManagedBy"
  value = "tfc"
}

resource "aws_servicecatalog_tag_option_resource_association" "example_product_name" {
  resource_id   = aws_servicecatalog_product.example.id
  tag_option_id = aws_servicecatalog_tag_option.product_name.id
}

resource "aws_servicecatalog_tag_option" "product_name" {
  key   = "ServiceCatalogProduct"
  value = aws_servicecatalog_product.example.name
}

resource "aws_servicecatalog_product_portfolio_association" "example" {
  for_each     = local.unique_portfolio_ids
  portfolio_id = each.value
  product_id   = aws_servicecatalog_product.example.id
}

# # # #
# THE PRODUCT'S LAUNCH CONSTRAINT AND IAM ROLE

resource "aws_servicecatalog_constraint" "example" {
  # Need to wait a bit after the role is created as Service Catalog will immediately try to assume the role to test it.
  depends_on = [time_sleep.wait_for_launch_constraint_role_to_be_assumable]

  for_each     = local.unique_portfolio_ids
  description  = "Launch constraint for the ${aws_servicecatalog_product.example.name} product."
  portfolio_id = each.value
  product_id   = aws_servicecatalog_product.example.id
  type         = "LAUNCH"

  parameters = jsonencode({
    "RoleArn" : aws_iam_role.example_product_launch_role.arn
  })
}

resource "aws_servicecatalog_principal_portfolio_association" "sagemaker_role_associations" {
  // Loop over the flattened list of portfolio-role pairs
  # for_each = {
  #   for pair in local.flattened_portfolio_role_pairs : "${pair.portfolio_id}-${pair.role_arn}" => pair
  # }
  for_each      = toset(var.sagemaker_user_role_arns)
  portfolio_id  = var.service_catalog_portfolio_ids[0]
  principal_arn = each.value
}

data "aws_iam_openid_connect_provider" "tfc_provider" {
  arn = var.tfc_provider_arn
}

resource "aws_iam_role" "example_product_launch_role" {
  name = "${local.class_case_product_name}LaunchRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # Allow Service Catalog to assume the role
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = "AllowServiceCatalogToAssume"
        Principal = {
          Service = "servicecatalog.amazonaws.com"
        }
      },
      {
        # Allow the SendApply and ParameterParser Lambda functions to assume the role so that they can download the provisioning artifact from S3
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Condition = {
          StringLike = {
            "aws:PrincipalArn" = [
              "${var.send_apply_lambda_role_arn}*",
              "${var.parameter_parser_role_arn}*"
            ]
          }
        }
      },
      {
        Action = "sts:AssumeRoleWithWebIdentity",
        Effect = "Allow",
        Principal = {
          Federated = var.tfc_provider_arn
        },
        Condition = {
          StringEquals = {
            "${var.tfc_hostname}:aud" = one(data.aws_iam_openid_connect_provider.tfc_provider.client_id_list)
          },
          StringLike = {
            "${var.tfc_hostname}:sub" = "organization:${var.tfc_organization}:project:${aws_servicecatalog_product.example.id}:workspace:*:run_phase:*"
          }
        }
      }
    ]
  })
}

resource "time_sleep" "wait_for_launch_constraint_role_to_be_assumable" {
  depends_on      = [aws_iam_role.example_product_launch_role, aws_iam_role_policy.example_product_launch_constraint_policy]
  create_duration = "15s"
}

resource "aws_iam_role_policy" "example_product_launch_constraint_policy" {
  name   = "example_product_launch_constraint_policy"
  role   = aws_iam_role.example_product_launch_role.id
  policy = data.aws_iam_policy_document.example_product_launch_constraint_policy.json
}

data "aws_iam_policy_document" "example_product_launch_constraint_policy" {
  version = "2012-10-17"

  statement {
    sid = "S3AccessToProvisioningObjects"

    effect = "Allow"

    actions = [
      "s3:GetObject",
    ]

    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "s3:ExistingObjectTag/servicecatalog:provisioning"
      values   = ["true"]
    }
  }

  statement {
    sid = "AllowCreationOfBucketsToDistributeProvisioningArtifact"

    effect = "Allow"

    actions = [
      "s3:CreateBucket*",
      "s3:DeleteBucket*",
      "s3:Get*",
      "s3:List*",
      "s3:PutBucketTagging"
    ]

    resources = ["arn:aws:s3:::*"]
  }

  statement {
    sid = "ResourceGroups"

    effect = "Allow"

    actions = [
      "resource-groups:CreateGroup",
      "resource-groups:ListGroupResources",
      "resource-groups:DeleteGroup",
      "resource-groups:Tag"
    ]

    resources = ["*"]
  }

  statement {
    sid = "Tagging"

    effect = "Allow"

    actions = [
      "tag:GetResources",
      "tag:GetTagKeys",
      "tag:GetTagValues",
      "tag:TagResources",
      "tag:UntagResources"
    ]

    resources = ["*"]
  }
}

