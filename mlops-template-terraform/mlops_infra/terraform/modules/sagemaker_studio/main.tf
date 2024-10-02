locals {
  domain_name           = var.domain_name
  auth_mode             = var.auth_mode
  vpc_id                = var.vpc_id
  subnet_ids            = var.subnet_ids
  sm_execution_role_arn = var.sm_execution_role_arn
  kms_key_arn           = var.kms_key_arn
  user_profile_names    = var.user_profile_names
  jupyter_app_name      = var.jupyter_app_name
}
##################################################################################################
# SageMaker Studio
##################################################################################################

resource "aws_sagemaker_domain" "mlops" {
  domain_name = local.domain_name
  auth_mode   = local.auth_mode
  vpc_id      = local.vpc_id
  subnet_ids  = local.subnet_ids

  default_user_settings {
    execution_role = local.sm_execution_role_arn
  }
  kms_key_id = local.kms_key_arn
}

resource "aws_sagemaker_user_profile" "mlops" {
  domain_id         = aws_sagemaker_domain.mlops.id
  for_each          = toset(local.user_profile_names)
  user_profile_name = each.key
}

resource "aws_sagemaker_app" "mlops" {
  depends_on = [
    aws_sagemaker_user_profile.mlops
  ]
  domain_id         = aws_sagemaker_domain.mlops.id
  for_each          = toset(local.user_profile_names)
  user_profile_name = each.key
  app_name          = local.jupyter_app_name
  app_type          = "JupyterServer"
}

resource "null_resource" "enable-projects-via-sdk" {
  depends_on = [
    aws_sagemaker_app.mlops
  ]
  provisioner "local-exec" {
    command     = "./modules/sagemaker_studio/scripts/enable-projects.py"
    interpreter = ["python3"]
    environment = {
      STUDIO_ROLE_ARN = local.sm_execution_role_arn
    }
  }
}
