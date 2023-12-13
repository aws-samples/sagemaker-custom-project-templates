resource "aws_ssm_parameter" "private_subnet_id" {
  name  = "private-subnets-ids"
  type  = "StringList"
  value = join(",", [aws_subnet.private.id, aws_subnet.private_2.id])
}

resource "aws_ssm_parameter" "sg_id" {
  name  = "sagemaker-domain-sg"
  type  = "String"
  value = aws_security_group.main.id
}