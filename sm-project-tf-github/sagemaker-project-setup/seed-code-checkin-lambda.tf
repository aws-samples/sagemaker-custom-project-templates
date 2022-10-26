#------------------------------------------------------#
# This component creates the Lambda Function to Perform 
# the Seed Code Checkin into the Source Repository
#------------------------------------------------------#


#------------------------------------------------------------------------------------------#
# Create data files for AWS Lambda Function to trigger Seed Code Checkin CodeBuild Project 
#------------------------------------------------------------------------------------------#

data "external" "build_dir" {
  program = ["bash", "${path.module}/bin/dir_md5.sh", "${local.lambda_files}/"]
}

resource "null_resource" "remove_lambda_zip" {
  triggers = {
    build_folder_content_md5 = data.external.build_dir.result.md5
  }
  provisioner "local-exec" {
    command = "/bin/rm -rf ${local.output_files}/${local.cmn_res_name}.zip;"
  }
}

data "template_file" "t_file" {
  count    = length(local.source_files)
  template = file(element(local.source_files, count.index))
}

data "archive_file" "update_lambda_zip" {
  depends_on  = [null_resource.remove_lambda_zip]
  type        = "zip"
  output_path = "${local.output_files}/${local.cmn_res_name}.zip"
  source {
    filename = basename(local.source_files[0])
    content  = data.template_file.t_file.0.rendered
  }
}


#--------------------------------------------------------------------------#
# Create AWS Lambda Function to trigger Seed Code Checkin CodeBuild Project 
#--------------------------------------------------------------------------#

resource "aws_lambda_function" "seed_code_checkin_build_trigger" {
  depends_on       = [data.archive_file.update_lambda_zip, aws_codebuild_project.seed_code_checkin_build]
  function_name    = "${local.cmn_res_name}-seed-code-checkin"
  description      = "To trigger the codebuild project for the seedcode checkin"
  role             = "arn:aws:iam::${local.account_id}:${var.sagemaker_service_catalog_lambda_role}"
  handler          = "app.lambda_handler"
  runtime          = "python3.8"
  filename         = data.archive_file.update_lambda_zip.output_path
  source_code_hash = data.archive_file.update_lambda_zip.output_base64sha256
  timeout          = 900
  memory_size      = 1024
  tags             = local.common_tags

  environment {
    variables = {
      CodeBuildProjectName = aws_codebuild_project.seed_code_checkin_build.id
    }
  }
}


#--------------------------------------------------------------------------#
# Invoke the Seed Code Trigger Lambda Function
#--------------------------------------------------------------------------#

resource "aws_lambda_invocation" "seed_code_lambda_trigger" {

  function_name = aws_lambda_function.seed_code_checkin_build_trigger.function_name

  triggers = {
    redeployment = sha1(jsonencode([
      aws_lambda_function.seed_code_checkin_build_trigger.environment
    ]))
  }

  input = jsonencode({
    SEEDCODE_BUCKET_NAME          = var.seed_code_bucket_name
    SEEDCODE_BUCKET_KEY           = var.seed_code_bucket_key
    GIT_REPOSITORY_FULL_NAME      = var.git_repo_name
    GIT_REPOSITORY_BRANCH         = var.git_repo_branch
    GIT_REPOSITORY_CONNECTION_ARN = var.codestar_connection_arn
  })
}