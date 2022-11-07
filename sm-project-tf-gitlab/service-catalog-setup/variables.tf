# Variables
#------------
variable "region" {
  description = "AWS region identifier"
}

variable "env" {
  description = "Name of the environment the infrastructure is for"
}

variable "organization" {
  description = "Name of the organization the infrastructure is for"
}

variable "role" {
  description = "Name or role of the component or subcomponent"
}

variable "sc_portfolio_owner" {
  description = "Owner of Service Catalog Portfolio Owner"
}

variable "sc_product_owner" {
  description = "Owner of Service Catalog Product Owner"
}

variable "sc_product_launch_role" {
  description = "IAM role for the SC Product Launch"
}

variable "sc_portfolio_service_role" {
  description = "IAM role for the SC Portfolio"
}

variable "backend_table_prefix" {
  description = "DynamoDB Backend Table"
}

variable "cm_exec_pass_role_arn" {
  description = "IAM Pass Role resource for Command Runner Exec Role"
}

variable "command_runner_exec_role" {
  description = "IAM Role assumed by CloudFormation Command Runner"
}

variable "gitlab_private_token" {
  description = "Gitlab Private Token"
}

