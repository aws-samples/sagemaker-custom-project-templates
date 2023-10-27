resource "aws_kms_key" "key" {
  description         = var.description
  enable_key_rotation = true
  policy              = data.aws_iam_policy_document.key_policy.json
}

data "aws_iam_policy_document" "key_policy" {
  # checkov:skip=CKV_AWS_109:Key needs to be manageable by the Account root
  # checkov:skip=CKV_AWS_111:Key policies are already scoped to the key
  statement {
    principals {
      type        = "AWS"
      identifiers = var.trusted_accounts_for_decrypt_access
    }

    actions = [
      "kms:Decrypt",
    ]

    resources = [
      "*"
    ]
  }
  statement {
    principals {
      type        = "AWS"
      identifiers = [var.account_id]
    }

    actions = [
      "kms:*",
    ]

    resources = [
      "*"
    ]
  }
}