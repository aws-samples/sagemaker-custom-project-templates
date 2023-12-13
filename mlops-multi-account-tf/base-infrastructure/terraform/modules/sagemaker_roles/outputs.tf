output "data_scientist_role_arn" {
  value = aws_iam_role.data_scientist_role.arn
}
output "lead_data_scientist_role_arn" {
  value = aws_iam_role.lead_data_scientist_role.arn
}
output "sagemaker_studio_role_arn" {
  value = aws_iam_role.sagemaker_studio_role.arn
}