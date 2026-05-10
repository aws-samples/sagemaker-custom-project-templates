locals {
  prefix                         = var.prefix
  cidr_block                     = var.vpc_cidr_block
  private_subnet_cidr_block      = var.private_subnet_cidr_block
  public_subnet_cidr_block       = var.public_subnet_cidr_block
  availability_zone              = var.availability_zone
  enable_dns_hostnames           = var.enable_dns_hostnames
  vpc_name                       = "${local.prefix}-vpc"
  private_subnet_name            = "${local.vpc_name}-private-subnet"
  public_subnet_name             = "${local.vpc_name}-public-subnet"
  sagemaker_sg_name              = "${local.vpc_name}-sagemaker-sg"
  internet_gateway_name          = "${local.vpc_name}-ig-pub-priv"
  public_subnet_route_table_name = "${local.vpc_name}-route-table-for-ig"
  nat_gateway_name               = "${local.vpc_name}-nat-gateway"
  nat_gateway_route_table_name   = "${local.vpc_name}-rt-for-ng"
}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}


resource "aws_vpc" "mlops-test" {
  cidr_block           = local.cidr_block
  enable_dns_hostnames = local.enable_dns_hostnames
  tags = {
    Name = local.vpc_name
  }
}


##################################################################################################
# Private Subnet
##################################################################################################


resource "aws_subnet" "private" {

  depends_on = [
    aws_vpc.mlops-test,
    aws_subnet.public
  ]

  vpc_id                  = aws_vpc.mlops-test.id
  cidr_block              = local.private_subnet_cidr_block
  availability_zone       = local.availability_zone
  map_public_ip_on_launch = false
  tags = {
    Name = local.private_subnet_name
  }
}


resource "aws_security_group" "sagemaker_sg" {

  name        = local.sagemaker_sg_name
  description = local.sagemaker_sg_name
  vpc_id      = aws_vpc.mlops-test.id
  ingress {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
  }
  egress {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
  }
  tags = {
    "Name" = local.sagemaker_sg_name
  }
}


##################################################################################################
# Public Subnet
##################################################################################################

resource "aws_subnet" "public" {

  depends_on = [
    aws_vpc.mlops-test
  ]
  vpc_id                  = aws_vpc.mlops-test.id
  cidr_block              = local.public_subnet_cidr_block
  availability_zone       = local.availability_zone
  map_public_ip_on_launch = true
  tags = {
    Name = local.public_subnet_name
  }
}


resource "aws_internet_gateway" "Internet_Gateway" {
  depends_on = [
    aws_vpc.mlops-test,
    aws_subnet.public,
    aws_subnet.private
  ]
  vpc_id = aws_vpc.mlops-test.id
  tags = {
    Name = local.internet_gateway_name
  }
}

resource "aws_route_table" "Public_Subnet_RT" {
  depends_on = [
    aws_vpc.mlops-test,
    aws_internet_gateway.Internet_Gateway
  ]

  vpc_id = aws_vpc.mlops-test.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.Internet_Gateway.id
  }

  tags = {
    Name = local.public_subnet_route_table_name
  }
}


resource "aws_route_table_association" "ig_rt_association" {

  depends_on = [
    aws_vpc.mlops-test,
    aws_subnet.public,
    aws_subnet.private,
    aws_route_table.Public_Subnet_RT
  ]
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.Public_Subnet_RT.id
}


##################################################################################################
# NAT Gateway
##################################################################################################

# Creating an Elastic IP for the NAT Gateway!
resource "aws_eip" "nat_gateway_eip" {
  depends_on = [
    aws_route_table_association.ig_rt_association
  ]
  vpc = true
}


# Creating a NAT Gateway!
resource "aws_nat_gateway" "nat_gateway" {
  depends_on = [
    aws_eip.nat_gateway_eip
  ]
  allocation_id = aws_eip.nat_gateway_eip.id
  subnet_id     = aws_subnet.public.id
  tags = {
    Name = local.nat_gateway_name
  }
}


resource "aws_route_table" "nat_gw_route_table" {
  depends_on = [
    aws_nat_gateway.nat_gateway
  ]

  vpc_id = aws_vpc.mlops-test.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat_gateway.id
  }

  tags = {
    Name = local.nat_gateway_route_table_name
  }

}


resource "aws_route_table_association" "nat_gw_route_table_Association" {
  depends_on = [
    aws_route_table.nat_gw_route_table
  ]
  subnet_id      = aws_subnet.private.id
  route_table_id = aws_route_table.nat_gw_route_table.id
}

##################################################################################################
# VPC Endpoints
##################################################################################################

resource "aws_vpc_endpoint" "codecommit" {
  vpc_id              = aws_vpc.mlops-test.id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.codecommit"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true
  security_group_ids  = [aws_security_group.sagemaker_sg.id]
  tags = {
    Name = "${local.vpc_name}-codecommit-vpce"
  }
}

resource "aws_vpc_endpoint" "git-codecommit" {
  vpc_id              = aws_vpc.mlops-test.id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.git-codecommit"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true
  security_group_ids  = [aws_security_group.sagemaker_sg.id]
  tags = {
    Name = "${local.vpc_name}-git-codecommit-vpce"
  }
}

resource "aws_vpc_endpoint" "sagemaker" {
  vpc_id             = aws_vpc.mlops-test.id
  service_name       = "aws.sagemaker.${data.aws_region.current.name}.notebook"
  vpc_endpoint_type  = "Interface"
  security_group_ids = [aws_security_group.sagemaker_sg.id]
  tags = {
    Name = "${local.vpc_name}-notebook-vpce"
  }
}

resource "aws_vpc_endpoint" "sagemaker-api" {
  vpc_id             = aws_vpc.mlops-test.id
  service_name       = "com.amazonaws.${data.aws_region.current.name}.sagemaker.api"
  vpc_endpoint_type  = "Interface"
  security_group_ids = [aws_security_group.sagemaker_sg.id]
  tags = {
    Name = "${local.vpc_name}-sm-api-vpce"
  }
}

resource "aws_vpc_endpoint" "sagemaker-runtime" {
  vpc_id             = aws_vpc.mlops-test.id
  service_name       = "com.amazonaws.${data.aws_region.current.name}.sagemaker.runtime"
  vpc_endpoint_type  = "Interface"
  security_group_ids = [aws_security_group.sagemaker_sg.id]
  tags = {
    Name = "${local.vpc_name}-sm-runtime-vpce"
  }
}

resource "aws_vpc_endpoint" "ecr" {
  vpc_id             = aws_vpc.mlops-test.id
  service_name       = "com.amazonaws.${data.aws_region.current.name}.ecr.api"
  vpc_endpoint_type  = "Interface"
  security_group_ids = [aws_security_group.sagemaker_sg.id]
  tags = {
    Name = "${local.vpc_name}-ecr-api-vpce"
  }
}

resource "aws_vpc_endpoint" "ecr_docker" {
  vpc_id             = aws_vpc.mlops-test.id
  service_name       = "com.amazonaws.${data.aws_region.current.name}.ecr.dkr"
  vpc_endpoint_type  = "Interface"
  security_group_ids = [aws_security_group.sagemaker_sg.id]
  tags = {
    Name = "${local.vpc_name}-ecr-dkr-vpce"
  }
}

resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.mlops-test.id
  service_name      = "com.amazonaws.${data.aws_region.current.name}.s3"
  vpc_endpoint_type = "Gateway"
  tags = {
    Name = "${local.vpc_name}-s3-vpce"
  }
}

resource "aws_vpc_endpoint" "kms" {
  vpc_id             = aws_vpc.mlops-test.id
  service_name       = "com.amazonaws.${data.aws_region.current.name}.kms"
  vpc_endpoint_type  = "Interface"
  security_group_ids = [aws_security_group.sagemaker_sg.id]
  tags = {
    Name = "${local.vpc_name}-kms-vpce"
  }
}

resource "aws_vpc_endpoint" "cloudwatch" {
  vpc_id             = aws_vpc.mlops-test.id
  service_name       = "com.amazonaws.${data.aws_region.current.name}.monitoring"
  vpc_endpoint_type  = "Interface"
  security_group_ids = [aws_security_group.sagemaker_sg.id]
  tags = {
    Name = "${local.vpc_name}-cloudwatch-vpce"
  }
}

resource "aws_vpc_endpoint" "cloudwatch_logs" {
  vpc_id             = aws_vpc.mlops-test.id
  service_name       = "com.amazonaws.${data.aws_region.current.name}.logs"
  vpc_endpoint_type  = "Interface"
  security_group_ids = [aws_security_group.sagemaker_sg.id]
  tags = {
    Name = "${local.vpc_name}-cloudwatch-logs-vpce"
  }
}
