resource "aws_vpc_endpoint" "sagemaker_studio" {
  vpc_id             = aws_vpc.main.id
  subnet_ids         = [aws_subnet.private.id, aws_subnet.private_2.id]
  service_name       = "aws.sagemaker.${var.region}.studio"
  vpc_endpoint_type  = "Interface"
  security_group_ids = [aws_security_group.main.id]
}
resource "aws_vpc_endpoint" "sagemaker_runtime" {
  vpc_id             = aws_vpc.main.id
  subnet_ids         = [aws_subnet.private.id, aws_subnet.private_2.id]
  service_name       = "com.amazonaws.${var.region}.sagemaker.runtime"
  vpc_endpoint_type  = "Interface"
  security_group_ids = [aws_security_group.main.id]
}
resource "aws_vpc_endpoint" "sts" {
  vpc_id             = aws_vpc.main.id
  subnet_ids         = [aws_subnet.private.id, aws_subnet.private_2.id]
  service_name       = "com.amazonaws.${var.region}.sts"
  vpc_endpoint_type  = "Interface"
  security_group_ids = [aws_security_group.main.id]
}
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"
}
resource "aws_vpc_endpoint" "service_catalog" {
  vpc_id             = aws_vpc.main.id
  subnet_ids         = [aws_subnet.private.id, aws_subnet.private_2.id]
  service_name       = "com.amazonaws.${var.region}.servicecatalog"
  vpc_endpoint_type  = "Interface"
  security_group_ids = [aws_security_group.main.id]
}
resource "aws_vpc_endpoint" "sagemaker_api" {
  vpc_id             = aws_vpc.main.id
  subnet_ids         = [aws_subnet.private.id, aws_subnet.private_2.id]
  service_name       = "com.amazonaws.${var.region}.sagemaker.api"
  vpc_endpoint_type  = "Interface"
  security_group_ids = [aws_security_group.main.id]
}

resource "aws_vpc_endpoint" "logs" {
  vpc_id             = aws_vpc.main.id
  subnet_ids         = [aws_subnet.private.id, aws_subnet.private_2.id]
  service_name       = "com.amazonaws.${var.region}.logs"
  vpc_endpoint_type  = "Interface"
  security_group_ids = [aws_security_group.main.id]
}

resource "aws_vpc_endpoint" "events" {
  vpc_id             = aws_vpc.main.id
  subnet_ids         = [aws_subnet.private.id, aws_subnet.private_2.id]
  service_name       = "com.amazonaws.${var.region}.events"
  vpc_endpoint_type  = "Interface"
  security_group_ids = [aws_security_group.main.id]
}

