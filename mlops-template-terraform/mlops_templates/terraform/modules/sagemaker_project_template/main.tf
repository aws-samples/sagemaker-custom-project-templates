locals {
  template_name                = var.template_name
  template_key                 = var.template_key
  template_local_path          = var.template_local_path
  seed_code_map                = var.seed_code_map
  template_vars                = var.template_vars
  sm_execution_role_arn        = var.sagemaker_execution_role_arn
  owner                        = var.owner
  sagemaker_execution_role_arn = var.sagemaker_execution_role_arn
}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

resource "aws_s3_bucket" "sc_bucket" {
  bucket = "${replace(local.template_name, "_", "-")}-${data.aws_caller_identity.current.account_id}-${data.aws_region.current.name}-service-catalog"
}

resource "aws_s3_bucket_acl" "private_acl" {
  bucket = aws_s3_bucket.sc_bucket.id
  acl    = "private"
}


data "archive_file" "seed_source" {
  for_each    = local.seed_code_map
  type        = "zip"
  source_dir  = each.value.local_path
  output_path = "${each.value.local_path}.zip"
}

resource "aws_s3_bucket_object" "seed_code_archive" {
  depends_on = [
    aws_s3_bucket.sc_bucket,
    data.archive_file.seed_source
  ]
  for_each = local.seed_code_map
  bucket   = aws_s3_bucket.sc_bucket.id
  key      = each.value.key
  source   = "${each.value.local_path}.zip"
  etag     = filemd5("${each.value.local_path}.zip")
}
resource "local_file" "template_out" {
    content  = templatefile("${local.template_local_path}", merge({ seed_code_bucket = aws_s3_bucket.sc_bucket.id}, local.template_vars))
    filename = "${path.module}/.terraform.out/generated_template.yaml"
}


resource "aws_s3_bucket_object" "service_catalog_mlops_template" {
  depends_on = [
    aws_s3_bucket.sc_bucket
  ]
  bucket  = aws_s3_bucket.sc_bucket.id
  key     = local.template_key
  content = templatefile("${local.template_local_path}", merge({ seed_code_bucket = aws_s3_bucket.sc_bucket.id}, local.template_vars))
}

resource "aws_servicecatalog_product" "mlops_product" {
  depends_on = [
    aws_s3_bucket_object.service_catalog_mlops_template
  ]

  name = local.template_name
  owner = local.owner
  type  = "CLOUD_FORMATION_TEMPLATE"

  provisioning_artifact_parameters {
    type         = "CLOUD_FORMATION_TEMPLATE"
    template_url = "https://${aws_s3_bucket.sc_bucket.id}.s3.amazonaws.com/${local.template_key}"
  }

  tags = {
    "sagemaker:studio-visibility" = "true"
  }
}


resource "aws_iam_role" "service_launch_role" {
  name = "service_launch_role"
  path = "/service-role/"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = "AllowRoleAssume"
        Principal = {
          Service = "servicecatalog.amazonaws.com"
        }
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "aws_sagemaker_full_access" {
  role       = aws_iam_role.service_launch_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerAdmin-ServiceCatalogProductsServiceRolePolicy"
}

resource "aws_servicecatalog_portfolio" "projects_templates" {
  name          = "${local.template_name}-portfolio"
  description   = "${local.template_name}: Terraform SageMaker Project Templates"
  provider_name = local.owner
  tags = {
    "sagemaker:studio-visibility" = "true"
  }
}

resource "aws_servicecatalog_product_portfolio_association" "template_association" {
  portfolio_id = aws_servicecatalog_portfolio.projects_templates.id
  product_id   = aws_servicecatalog_product.mlops_product.id
}

resource "aws_servicecatalog_principal_portfolio_association" "sm_execution_role_principal_association" {
  portfolio_id  = aws_servicecatalog_portfolio.projects_templates.id
  principal_arn = local.sagemaker_execution_role_arn
}

# resource "aws_servicecatalog_constraint" "sm_execution_role_launch_constraint" {
#   description  = "${local.template_name} - constraint launch to Sagemaker execution role"
#   portfolio_id = aws_servicecatalog_portfolio.projects_templates.id
#   product_id   = aws_servicecatalog_product.mlops_product.id
#   type         = "LAUNCH"

#   parameters = jsonencode({
#     "RoleArn" : local.sagemaker_execution_role_arn
#   })
# }

