#--------------------------------------------------------------------------------------------#
# This component will create the Service Catalog resources required for the SageMaker Projects
#--------------------------------------------------------------------------------------------#

#----------------------------------------------------------------#
# Create AWS Service Catalog Portfolio
#----------------------------------------------------------------#

resource "aws_servicecatalog_portfolio" "mlops_sc_portfolio" {
  name          = local.cmn_res_name
  description   = "Portfolio of products for Amazon Sagemaker Projects"
  provider_name = var.sc_portfolio_owner
}

#----------------------------------------------------------------#
# Create AWS Service Catalog Product
#----------------------------------------------------------------#

resource "aws_servicecatalog_product" "mlops_tf_sc_product" {
  depends_on  = [aws_s3_object.sm_project_cfn]
  description = "MLOps pipeline with GitHub and AWS CodePipeline deployed from Terraform"
  name        = local.cmn_res_name
  owner       = var.sc_product_owner
  type        = "CLOUD_FORMATION_TEMPLATE"

  provisioning_artifact_parameters {
    template_url = "https://${aws_s3_bucket.terraform_data_source_s3.id}.s3.${var.region}.amazonaws.com/${aws_s3_object.sm_project_cfn.id}"
    type         = "CLOUD_FORMATION_TEMPLATE"
  }

  tags = {
    "sagemaker:studio-visibility" = "true"
  }

}

#----------------------------------------------------------------#
# Associate the Service Catalog Product and Portfolio
#----------------------------------------------------------------#

resource "aws_servicecatalog_product_portfolio_association" "mlops_sc_assocation" {
  depends_on   = [aws_servicecatalog_product.mlops_tf_sc_product, aws_servicecatalog_portfolio.mlops_sc_portfolio]
  portfolio_id = aws_servicecatalog_portfolio.mlops_sc_portfolio.id
  product_id   = aws_servicecatalog_product.mlops_tf_sc_product.id
}

#----------------------------------------------------------------#
# Add Launch Constraint to the Service Catalog Product
#----------------------------------------------------------------#

resource "aws_servicecatalog_constraint" "mlops_sc_constraint" {
  depends_on   = [aws_servicecatalog_product_portfolio_association.mlops_sc_assocation]
  description  = "IAM Role for launching the MLOps SC product"
  portfolio_id = aws_servicecatalog_portfolio.mlops_sc_portfolio.id
  product_id   = aws_servicecatalog_product.mlops_tf_sc_product.id
  type         = "LAUNCH"

  parameters = jsonencode({
    "RoleArn" : aws_iam_role.sc_launch_iam_role.arn
  })
}


#----------------------------------------------------------------#
# Add IAM role to the Service Catalog Portfolio
#----------------------------------------------------------------#

resource "aws_servicecatalog_principal_portfolio_association" "sc_portfolio_iam_role" {
  depends_on    = [aws_servicecatalog_constraint.mlops_sc_constraint]
  portfolio_id  = aws_servicecatalog_portfolio.mlops_sc_portfolio.id
  principal_arn = "arn:aws:iam::${local.account_id}:${var.sc_portfolio_service_role}"
}
