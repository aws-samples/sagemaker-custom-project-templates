variable "prefix" {
  type        = string
  description = "Naming prefix to use for resources"
}

variable "vpc_cidr_block" {
  type        = string
  description = "CIRD block for VPC"
  default     = "10.0.0.0/16"
}

variable "private_subnet_cidr_block" {
  type        = string
  description = "CIDR block for private subnets"
  default     = "10.0.1.0/24"
}

variable "public_subnet_cidr_block" {
  type        = string
  description = "CIDR block for public subnets"
  default     = "10.0.0.0/24"
}

variable "availability_zone" {
  type        = string
  description = "Availability Zone for Subnets"
  default     = "eu-west-1a"
}

variable "enable_dns_hostnames" {
  type        = bool
  description = "Enable DNS hostnames for the VPC"
  default     = true
}
