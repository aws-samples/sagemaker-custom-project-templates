#---------------------------------------------------------------------------------------#
# This Terraform component will copy the Amazon SageMaker project files to the S3 bucket
# The files include:
# - CFN YAML file  used to create the Service Catalog Product
# - Zip of Terraform Code that will be executed during SageMaker Project Creation
#---------------------------------------------------------------------------------------#

resource "aws_s3_object" "sm_project_cfn" {
  bucket = aws_s3_bucket.terraform_data_source_s3.id
  key    = local.cfn_sm_key
  source = "${local.cfn_folder}/${local.cfn_sm_key}"
  etag   = filemd5("${local.cfn_folder}/${local.cfn_sm_key}")
}

resource "aws_s3_object" "s3_tf_code_zip" {
  depends_on = [data.archive_file.update_tf_code_zip, aws_s3_object.sm_project_cfn]
  bucket     = aws_s3_bucket.terraform_data_source_s3.id
  key        = "${local.output_tf_zip_folder}.zip"
  source     = "${local.output_files}/${local.output_tf_zip_folder}.zip"
  # etag   = filemd5("${local.output_files}/${local.output_tf_zip_folder}.zip")
}