resource "aws_ssm_parameter" "ssm_sg_ds_role" {
  name  = "/mlops/role/ds"
  type  = "String"
  value = aws_iam_role.data_scientist_role.arn
}
resource "aws_ssm_parameter" "ssm_sg_lead_role" {
  name  = "/mlops/role/lead"
  type  = "String"
  value = aws_iam_role.lead_data_scientist_role.arn
}
resource "aws_ssm_parameter" "ssm_sg_execution_role" {
  name  = "/mlops/role/execution"
  type  = "String"
  value = aws_iam_role.sagemaker_studio_role.arn
}