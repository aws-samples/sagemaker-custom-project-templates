# Creates policy document s3 projects buckets
data "aws_iam_policy_document" "s3_projects_bucket_policy" {
  statement {
    sid       = "DenyUnEncryptedObjectTransfers"
    effect    = "Deny"
    resources = ["arn:aws:s3:::${module.sagemaker_projects_bucket.bucket_id}/*"]
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
