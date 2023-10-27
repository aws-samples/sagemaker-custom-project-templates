output "sg_id" {
  value = aws_security_group.main.id
}
output "vpc_id" {
  value = aws_vpc.main.id
}
output "private_subnet_id" {
  value = aws_subnet.private.id
}

output "private_subnet_2_id" {
  value = aws_subnet.private_2.id
}
