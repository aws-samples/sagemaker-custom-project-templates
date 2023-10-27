resource "aws_servicecatalog_portfolio" "sagemaker_portfolio" {
  name          = "Sagemaker Porfolio"
  description   = "Used Internally by Sagemaker while creating projects"
  provider_name = "${var.environment}-SageMaker"
}

resource "aws_s3_object" "template_object" {
  for_each = var.templates
  bucket   = var.bucket_id
  key      = "${each.value.file}.yaml"
  source   = "./sagemaker_templates/${each.value.file}.yaml"
  etag     = filemd5("./sagemaker_templates/${each.value.file}.yaml")
}

resource "aws_servicecatalog_product" "product" {
  for_each    = var.templates
  name        = each.value.name
  description = each.value.description
  owner       = "${var.environment}-SageMaker"
  type        = "CLOUD_FORMATION_TEMPLATE"
  provisioning_artifact_parameters {
    template_url = "https://${var.bucket_domain_name}/${aws_s3_object.template_object[each.key].id}"
    name         = "delete_me_1"
    type         = "CLOUD_FORMATION_TEMPLATE"
  }
  tags = {
    "sagemaker:studio-visibility" = "true"
  }
}

resource "aws_servicecatalog_provisioning_artifact" "artifact" {
  for_each     = var.templates
  name         = "latest"
  type         = "CLOUD_FORMATION_TEMPLATE"
  template_url = "https://${var.bucket_domain_name}/${aws_s3_object.template_object[each.key].key}?version_id=${aws_s3_object.template_object[each.key].version_id}"
  product_id   = aws_servicecatalog_product.product[each.key].id
}

resource "aws_servicecatalog_product_portfolio_association" "sagemaker_product_to_portfolio" {
  for_each     = var.templates
  portfolio_id = aws_servicecatalog_portfolio.sagemaker_portfolio.id
  product_id   = aws_servicecatalog_product.product[each.key].id
}

resource "aws_servicecatalog_principal_portfolio_association" "sagemaker" {
  portfolio_id  = aws_servicecatalog_portfolio.sagemaker_portfolio.id
  principal_arn = var.lead_data_scientist_execution_role_arn
}

resource "aws_servicecatalog_constraint" "constraint" {
  for_each     = var.templates
  description  = "contraint for launch sagemaker project"
  portfolio_id = aws_servicecatalog_portfolio.sagemaker_portfolio.id
  product_id   = aws_servicecatalog_product.product[each.key].id
  type         = "LAUNCH"
  parameters = jsonencode({
    "RoleArn" : "${var.launch_role}"
  })
}
