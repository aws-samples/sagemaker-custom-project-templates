#------------------------------------------------------------#
# Create AWS SageMaker repo from the ML Source Code repository
#------------------------------------------------------------#

resource "aws_sagemaker_code_repository" "sagemaker_model_build_repo" {
  code_repository_name = "sagemaker-${var.sagemaker_project_id}-modelbuild"
  tags                 = { "sagemaker:project-name" : var.sagemaker_project_name, "sagemaker:project-id" : var.sagemaker_project_id }

}