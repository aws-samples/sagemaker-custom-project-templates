#----------------------------------------------------------------------------------#
# This terraform component will create S3 Bucket  
# 
# The bucket will store the SageMaker Project artifacts
#----------------------------------------------------------------------------------#


resource "aws_s3_bucket" "terraform_data_source_s3" {
  bucket = local.cmn_res_name
  tags   = local.common_tags
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_data_source_s3_sse" {
  bucket = aws_s3_bucket.terraform_data_source_s3.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_data_source_s3_block_public_access" {
  bucket                  = aws_s3_bucket.terraform_data_source_s3.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}