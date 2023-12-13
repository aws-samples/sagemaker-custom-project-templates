# IAM policy
resource "aws_iam_policy" "deny_sagemaker_jobs_outside_vpc" {
  name        = "deny_sagemaker_jobs_outside_vpc"
  description = "Perms deny for running sagemaker jobs outside vpc."
  policy      = data.aws_iam_policy_document.deny_sagemaker_jobs_outside_vpc.json

}

resource "aws_iam_policy" "sagemaker_projects_s3_policy" {
  name        = "sagemaker_projects_s3_policy"
  description = "Giving access to ML platform buckets."
  policy      = data.aws_iam_policy_document.sagemaker_projects_s3_policy.json

}

resource "aws_iam_policy" "sagemaker_pass_role_policy" {
  name        = "sagemaker_pass_role_policy"
  description = "Perms pass role policy."
  policy      = data.aws_iam_policy_document.sagemaker_pass_role_policy.json
}

# Role
resource "aws_iam_role" "sagemaker_execution_role" {
  name               = "sagemaker_execution_role"
  assume_role_policy = data.aws_iam_policy_document.sagemaker_assume_role_policy.json
  managed_policy_arns = [
    aws_iam_policy.deny_sagemaker_jobs_outside_vpc.arn,
    aws_iam_policy.sagemaker_pass_role_policy.arn,
    aws_iam_policy.sagemaker_projects_s3_policy.arn,
    "arn:aws:iam::aws:policy/AmazonSSMReadOnlyAccess",
    "arn:aws:iam::aws:policy/CloudWatchFullAccess",
    "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess",
    "arn:aws:iam::aws:policy/AmazonSSMReadOnlyAccess",
    "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess",
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  ]
}