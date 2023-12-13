# Creates policy document for sagemaker bucket
data "aws_iam_policy_document" "sagemaker_bucket_policy" {
  statement {
    sid       = "DenyUnEncryptedObjectTransfers"
    effect    = "Deny"
    resources = ["arn:aws:s3:::${module.sagemaker_bucket.bucket_id}/*"]
    actions   = ["s3:*"]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }

    principals {
      type        = "*"
      identifiers = ["*"]
    }
  }
}


# Creates policy document for datascience bucket
data "aws_iam_policy_document" "datascience_bucket_policy" {
  statement {
    sid       = "DenyUnEncryptedObjectTransfers"
    effect    = "Deny"
    resources = ["arn:aws:s3:::${module.datascience_bucket.bucket_id}/*"]
    actions   = ["s3:*"]
    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }

    principals {
      type        = "*"
      identifiers = ["*"]
    }
  }
}


# Creates policy document for service catalog bucket
data "aws_iam_policy_document" "service_catalog_bucket_policy" {
  statement {
    sid       = "DenyUnEncryptedObjectTransfers"
    effect    = "Deny"
    resources = ["arn:aws:s3:::${module.service_catalog_bucket.bucket_id}/*"]
    actions   = ["s3:*"]
    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }

    principals {
      type        = "*"
      identifiers = ["*"]
    }
  }
}


# Creates policy document for kms key
data "aws_iam_policy_document" "sagemaker_key_policy" {

  statement {
    sid       = "Allow access for Key Administrators"
    effect    = "Allow"
    actions   = ["kms:*"]
    resources = ["*"]

    principals {
      type = "AWS"
      identifiers = [
        "arn:aws:iam::${local.account_id}:root",
      ]
    }
  }

  statement {
    sid    = "Allow use of the key"
    effect = "Allow"
    actions = [
      "kms:Encrypt",
      "kms:Decrypt",
      "kms:ReEncrypt*",
      "kms:GenerateDataKey*",
      "kms:DescribeKey",
      "kms:CreateGrant",
      "kms:ListGrants",
      "kms:RevokeGrant"
    ]
    resources = ["*"]

    principals {
      type = "AWS"
      identifiers = [
        "arn:aws:iam::${local.account_id}:root",
        "${module.sagemaker_roles.data_scientist_role_arn}",
        "${module.sagemaker_roles.lead_data_scientist_role_arn}"
      ]
    }
  }
}
