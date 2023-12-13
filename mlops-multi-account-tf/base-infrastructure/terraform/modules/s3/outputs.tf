output "bucket_id" {
  description = "The name of the bucket."
  value       = aws_s3_bucket.bucket.id
}

output "bucket_arn" {
  description = "The ARN of the bucket. Will be of format arn:aws:s3:::bucketname."
  value       = aws_s3_bucket.bucket.arn
}

output "s3_bucket_region" {
  description = "The AWS region this bucket resides in."
  value       = aws_s3_bucket.bucket.region
}

output "s3_bucket_domain_name" {
  description = "The AWS region this bucket resides in."
  value       = aws_s3_bucket.bucket.bucket_domain_name
}