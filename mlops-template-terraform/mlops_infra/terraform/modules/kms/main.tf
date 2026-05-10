locals {
  kms_key_alias = var.kms_key_alias
}

data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "sm_key_policy" {
  statement {
    sid    = "Allow use of the key"
    effect = "Allow"
    actions = [
      "kms:*"
    ]
    resources = ["*"]

    principals {
      type = "AWS"
      identifiers = [
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
      ]
    }
  }
}

resource "aws_kms_key" "sm_kms" {
  description = "KMS key to encrypt/decrypt for SageMaker"
  policy      = data.aws_iam_policy_document.sm_key_policy.json
}

# Add an alias to the key
resource "aws_kms_alias" "sm_kms" {
  name          = "alias/${local.kms_key_alias}"
  target_key_id = aws_kms_key.sm_kms.key_id
}
