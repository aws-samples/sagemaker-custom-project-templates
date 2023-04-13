#------------------------------------------------------#
# This component creates the Lambda Function to Perform 
# the Seed Code Checkin into the Source Repository
#------------------------------------------------------#


#------------------------------------------------------------------------------------------#
# Create data files for AWS Lambda Function to trigger Seed Code Checkin  
#------------------------------------------------------------------------------------------#

data "external" "build_dir" {
  program = ["bash", "${path.module}/bin/dir_md5.sh", "${local.lambda_files}/lambda-seedcode-checkin-gitlab/"]
}

resource "null_resource" "remove_seedcode_lambda_zip" {
  triggers = {
    build_folder_content_md5 = data.external.build_dir.result.md5
  }
  provisioner "local-exec" {
    command = "/bin/rm -rf ${local.output_files}/${local.cmn_res_name}-seedcode.zip;"
  }
}

data "archive_file" "seedcode_lambda_zip" {
  depends_on  = [null_resource.remove_seedcode_lambda_zip]
  type        = "zip"
  output_path = "${local.output_files}/${local.cmn_res_name}-seedcode.zip"
  source_dir  = "${local.lambda_files}/lambda-seedcode-checkin-gitlab/"
}

#------------------------------------------------------------------------------------------#
# Create data files for AWS Lambda Function to trigger GitLab Pipeline 
#------------------------------------------------------------------------------------------#

data "external" "pipeline_dir" {
  program = ["bash", "${path.module}/bin/dir_md5.sh", "${local.lambda_files}/lambda-gitlab-pipeline-trigger/"]
}

resource "null_resource" "remove_pipeline_lambda_zip" {
  triggers = {
    build_folder_content_md5 = data.external.build_dir.result.md5
  }
  provisioner "local-exec" {
    command = "/bin/rm -rf ${local.output_files}/${local.cmn_res_name}-pipeline.zip;"
  }
}

data "archive_file" "pipeline_lambda_zip" {
  depends_on  = [null_resource.remove_pipeline_lambda_zip]
  type        = "zip"
  output_path = "${local.output_files}/${local.cmn_res_name}-pipeline.zip"
  source_dir  = "${local.lambda_files}/lambda-gitlab-pipeline-trigger/"
}


#--------------------------------------------------------------------------#
# Create AWS Lambda Function to trigger Seed Code Checkin 
#--------------------------------------------------------------------------#

resource "aws_lambda_function" "seed_code_checkin_build_trigger" {
  depends_on       = [data.archive_file.seedcode_lambda_zip]
  function_name    = "${local.cmn_res_name}-seed-code-checkin"
  description      = "To trigger the codebuild project for the seedcode checkin"
  role             = "arn:aws:iam::${local.account_id}:${var.sagemaker_service_catalog_lambda_role}"
  handler          = "app.lambda_handler"
  runtime          = "python3.8"
  filename         = data.archive_file.seedcode_lambda_zip.output_path
  source_code_hash = data.archive_file.seedcode_lambda_zip.output_base64sha256
  timeout          = 900
  memory_size      = 1024
  tags             = local.common_tags

  environment {
    variables = {
      GitLabTokenSecretName    = var.secrets_manager_gitlab_secret_name
      Region                   = var.region
      GitLabServer             = var.gitlab_url
      BuildProjectName         = var.git_build_repo_name
      DeployProjectName        = var.git_deploy_repo_name
      GitlabBuildRepoBranch    = var.git_build_repo_branch
      GitlabDeployRepoBranch   = var.git_deploy_repo_branch
      SageMakerPipelineRoleArn = "arn:aws:iam::${local.account_id}:${var.sagemaker_service_catalog_exec_role}"
      SageMakerProjectName     = var.sagemaker_project_name
      SageMakerProjectId       = var.sagemaker_project_id
      IAMAccessKeySecretName   = var.secrets_manager_gitlab_iam_access_key
      IAMSecretKeySecretName   = var.secrets_manager_gitlab_iam_secret_key
      AccountId                = local.account_id
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
    GIT_REPOSITORY_FULL_NAME = var.git_build_repo_name
    GIT_REPOSITORY_BRANCH    = var.git_build_repo_branch
  })
}


#--------------------------------------------------------------------------#
# Create AWS Lambda Function to trigger GitLab deploy pipeline
#--------------------------------------------------------------------------#

resource "aws_lambda_function" "deploy_pipeline" {
  depends_on       = [data.archive_file.pipeline_lambda_zip]
  function_name    = "${local.cmn_res_name}-deploy-pipeline"
  description      = "To trigger the codebuild project for the Gitlab deploy pipeline"
  role             = "arn:aws:iam::${local.account_id}:${var.sagemaker_service_catalog_lambda_role}"
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.8"
  filename         = data.archive_file.pipeline_lambda_zip.output_path
  source_code_hash = data.archive_file.pipeline_lambda_zip.output_base64sha256
  timeout          = 900
  memory_size      = 1024
  tags             = local.common_tags

  environment {
    variables = {
      GitLabTokenSecretName  = var.secrets_manager_gitlab_secret_name
      Region                 = var.region
      GitLabServer           = var.gitlab_url
      DeployProjectName      = var.git_deploy_repo_name
      GitlabDeployRepoBranch = var.git_deploy_repo_branch
      SageMakerProjectName   = var.sagemaker_project_name
      SageMakerProjectId     = var.sagemaker_project_id
    }
  }
}

#--------------------------------------------------------------------------#
# Create CloudWatch Event Rule to trigger the Lambda
#--------------------------------------------------------------------------#

resource "aws_cloudwatch_event_rule" "lambda_trigger_rule" {
  name        = "sagemaker-${var.sagemaker_project_name}-${var.sagemaker_project_id}-event-rule"
  description = "Rule to trigger a deployment when SageMaker Model registry is updated with a new model package."

  event_pattern = jsonencode({
    "source" : [
      "aws.sagemaker"
    ],
    "detail-type" : [
      "SageMaker Model Package State Change"
    ],
    "detail" : {
      "ModelPackageGroupName" : ["${var.sagemaker_project_name}-${var.sagemaker_project_id}"
      ],
      "ModelApprovalStatus" : [
        "Approved"
      ]
    }
  })
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.lambda_trigger_rule.name
  target_id = "sagemaker-${var.sagemaker_project_name}-trigger"
  arn       = aws_lambda_function.deploy_pipeline.arn
}


resource "aws_lambda_permission" "allow_cloudwatch" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.deploy_pipeline.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.lambda_trigger_rule.arn
}
