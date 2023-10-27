locals {
  encrypt = var.kms_key_id == "" ? 0 : 1
}

resource "aws_s3_bucket" "bucket" {
  #checkov:skip=CKV_AWS_19:v4 legacy
  #checkov:skip=CKV_AWS_18:v4 legacy
  #checkov:skip=CKV_AWS_145:v4 legacy
  #checkov:skip=CKV_AWS_21:v4 legacy
  #checkov:skip=CKV_AWS_144:v4 legacy
  #checkov:skip=CKV_AWS_52:v4 legacy
  bucket        = var.s3_bucket_name
  force_destroy = var.s3_bucket_force_destroy
}

resource "aws_s3_bucket_versioning" "bucket" {
  bucket = aws_s3_bucket.bucket.id
  versioning_configuration {
    status     = var.versioning
    mfa_delete = var.mfa_delete
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "artifacts_lifecycle" {
  bucket = aws_s3_bucket.bucket.id
  rule {
    id     = "bucket-lifecycle"
    status = "Enabled"
    transition {
      days          = var.days_to_intellegent_tiering
      storage_class = "INTELLIGENT_TIERING"
    }
    noncurrent_version_expiration {
      noncurrent_days = var.non_current_days_to_expire
    }
    noncurrent_version_transition {
      noncurrent_days = var.non_current_days_to_standard_ia
      storage_class   = "STANDARD_IA"
    }
    noncurrent_version_transition {
      noncurrent_days = var.non_current_days_to_glacier
      storage_class   = "GLACIER"
    }
    abort_incomplete_multipart_upload {
      days_after_initiation = var.abort_incomplete_upload
    }
  }
}

resource "aws_s3_bucket_policy" "bucket" {
  bucket = aws_s3_bucket.bucket.id
  policy = var.s3_bucket_policy
}
resource "aws_s3_bucket_server_side_encryption_configuration" "bucket" {
  count  = local.encrypt
  bucket = aws_s3_bucket.bucket.bucket

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = var.kms_key_id
      sse_algorithm     = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "bucket" {
  bucket                  = aws_s3_bucket.bucket.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}