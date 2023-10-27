resource "aws_ssm_parameter" "kms_key" {
  # checkov:skip=CKV2_AWS_34:SSM params should be encrypted
  name      = "/kms/key_arn"
  type      = "String"
  value     = aws_kms_key.key.arn
  overwrite = true
}
