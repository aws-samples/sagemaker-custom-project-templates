resource "aws_iam_role" "sagemaker_pipelines_execution_role" {
  name = local.sm_pipeline_execution_role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = "AllowRoleAssume"
        Principal = {
          Service = "sagemaker.amazonaws.com"
        }
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "aws_sagemaker_full_access" {
  role       = aws_iam_role.sagemaker_pipelines_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

resource "aws_iam_role_policy_attachment" "aws_sagemaker_s3_full_access" {
  role       = aws_iam_role.sagemaker_pipelines_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}