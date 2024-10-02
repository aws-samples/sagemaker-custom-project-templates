output "vpc_id" {
  value = aws_vpc.mlops-test.id
}

output "sg_id" {
  value = aws_security_group.sagemaker_sg.id
}

output "private_subnet_ids" {
  value = aws_subnet.private.id
}