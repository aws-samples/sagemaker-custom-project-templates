
resource "aws_sagemaker_domain" "sagemaker_domain" {
  domain_name             = var.studio_domain_name
  vpc_id                  = var.vpc_id
  subnet_ids              = [var.private_subnet_id, var.private_subnet_id_2]
  auth_mode               = "IAM"
  app_network_access_type = "VpcOnly"
  default_user_settings {
    execution_role  = var.sm_studio_role_arn
    security_groups = [var.sg_id]
    sharing_settings {
      notebook_output_option = "Disabled"
    }
  }
}

locals {
  users_ds       = yamldecode(file("../account_config/dev/data_scientist.yml")).users
  prefix_ds      = yamldecode(file("../account_config/dev/data_scientist.yml")).prefix
  users_lead_ds  = yamldecode(file("../account_config/dev/lead_data_scientist.yml")).users
  prefix_lead_ds = yamldecode(file("../account_config/dev/lead_data_scientist.yml")).prefix
}

resource "aws_sagemaker_user_profile" "data_scientist_sagemaker_user_profiles" {
  for_each          = { for user in local.users_ds : user.user_profile_name => user }
  user_profile_name = "${local.prefix_ds}-${each.value.user_profile_name}"
  domain_id         = aws_sagemaker_domain.sagemaker_domain.id
  user_settings {
    execution_role = var.data_scientist_execution_role_arn
  }
}

resource "aws_sagemaker_user_profile" "lead_data_scientist_sagemaker_user_profiles" {
  for_each          = { for user in local.users_lead_ds : user.user_profile_name => user }
  user_profile_name = "${local.prefix_lead_ds}-${each.value.user_profile_name}"
  domain_id         = aws_sagemaker_domain.sagemaker_domain.id
  user_settings {
    execution_role = var.lead_data_scientist_execution_role_arn
  }
}

resource "aws_sagemaker_servicecatalog_portfolio_status" "enable_sagemaker_servicecatalog_portfolio" {
  status = "Enabled"
}
