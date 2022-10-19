output "kms_key_id" {
  value = aws_kms_key.sm_kms.key_id
}

output "kms_key_arn" {
  value = aws_kms_key.sm_kms.arn
}

output "kms_key_alias" {
  value = aws_kms_alias.sm_kms.id
}
