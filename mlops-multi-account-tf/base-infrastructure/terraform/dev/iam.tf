## Policies
resource "aws_iam_policy" "sagemaker_pass_role_policy" {
  name        = "sagemaker_pass_role_policy"
  description = "Allowing passing of role to sagemaker service."
  policy      = data.aws_iam_policy_document.sagemaker_pass_role_policy.json
}

resource "aws_iam_policy" "sagemaker_execution_policy" {
  name        = "sagemaker_execution_policy"
  description = "All required SageMaker permissions for SageMaker Execution Role."
  policy      = data.aws_iam_policy_document.sagemaker_execution_policy.json
}

resource "aws_iam_policy" "sagemaker_execution_deny_policy" {
  name        = "sagemaker_execution_deny_policy"
  description = "Policy stopping default users from updating Model Registry that's part of automation,"
  policy      = data.aws_iam_policy_document.sagemaker_execution_deny_policy.json
}

resource "aws_iam_policy" "sagemaker_s3_policy" {
  name        = "sagemaker_s3_policy"
  description = "Giving access to ML platform buckets."
  policy      = data.aws_iam_policy_document.sagemaker_s3_policy.json
}

resource "aws_iam_policy" "sagemaker_vpc_policy" {
  name        = "sagemaker_vpc_policy"
  description = "Giving access to ML platform buckets."
  policy      = data.aws_iam_policy_document.sagemaker_vpc_policy.json
}

resource "aws_iam_policy" "sagemaker_related_policy" {
  name        = "sagemaker_related_policy"
  description = "Misc perms for SM execution role."
  policy      = data.aws_iam_policy_document.sagemaker_related_policy.json
}

resource "aws_iam_policy" "sagemaker_launch_service_catalog_policy" {
  name        = "sagemaker_launch_service_catalog_policy"
  description = "Perms to execute service catalog for SM execution role."
  policy      = data.aws_iam_policy_document.sagemaker_launch_service_catalog.json
}

resource "aws_iam_policy" "service_catalog_lambda_policy_resource" {
  name        = "service_catalog_lambda_role_policy_resource"
  description = "Perms for lambda execution role."
  policy      = data.aws_iam_policy_document.service_catalog_lambda_policy.json

}

resource "aws_iam_policy" "deny_sagemaker_jobs_outside_vpc" {
  name        = "deny_sagemaker_jobs_outside_vpc"
  description = "Perms deny for running sagemaker jobs outside vpc."
  policy      = data.aws_iam_policy_document.deny_sagemaker_jobs_outside_vpc.json
}




#Lambda clone repo and trigger workflow in service catalog
resource "aws_iam_role" "service_catalog_lambda_iam_role" {
  name               = "service_catalog_lambda_role"
  assume_role_policy = data.aws_iam_policy_document.service_catalog_lambda_assume_policy.json
  path               = "/service-role/"
  managed_policy_arns = [
    aws_iam_policy.service_catalog_lambda_policy_resource.arn
  ]

}

#Role Launch contraint service catalog
resource "aws_iam_role" "launch_constraint_iam_role" {
  name               = "launch_contraint_role"
  assume_role_policy = data.aws_iam_policy_document.servicecatalog_assume_role_policy.json
  managed_policy_arns = [
    aws_iam_policy.sagemaker_s3_policy.arn,
    aws_iam_policy.sagemaker_vpc_policy.arn,
    aws_iam_policy.sagemaker_launch_service_catalog_policy.arn
  ]
}
