data "aws_iam_policy_document" "codepipeline_assume_policy" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["codepipeline.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "codepipeline_role" {
  name               = "${local.prefix}-${local.sm_project_id}-codepipeline-modelbuild"
  assume_role_policy = data.aws_iam_policy_document.codepipeline_assume_policy.json
}


resource "aws_iam_policy" "code_pipeline_policy" {
  description = "pass_role_to_sm_pipelines for SM Pipelines for ${local.sm_project_id}"
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
        {
            "Action": [
                "s3:GetObject",
                "s3:GetObjectVersion",
                "s3:GetBucketVersioning"
            ],
            "Resource": [
                "arn:aws:s3:::${local.prefix}-*"
            ],
            "Effect": "Allow"
        },
        {
            "Action": [
                "s3:PutObject"
            ],
            "Resource": [
                "arn:aws:s3:::${local.prefix}-*"
            ],
            "Effect": "Allow"
        },
        {
            "Action": [
                "codecommit:CancelUploadArchive",
                "codecommit:GetBranch",
                "codecommit:GetCommit",
                "codecommit:GetUploadArchiveStatus",
                "codecommit:UploadArchive"
            ],
            "Resource": "${data.aws_codecommit_repository.repo.arn}",
            "Effect": "Allow"
        },
        {
            "Action": [
                "codebuild:BatchGetBuilds",
                "codebuild:StartBuild"
            ],
            "Resource": "${aws_codebuild_project.modelbuild_project.arn}",
            "Effect": "Allow"
        }
    ]
    }
EOF
}


resource "aws_iam_role_policy_attachment" "attach_code_pipeline_policy_to_role" {
  role       = aws_iam_role.codepipeline_role.name
  policy_arn = aws_iam_policy.code_pipeline_policy.arn
}

resource "aws_codepipeline" "codepipeline" {
  name     = local.pipeline_name
  role_arn = aws_iam_role.codepipeline_role.arn

  artifact_store {
    location = local.artifact_bucket_name
    type     = "S3"

    encryption_key {
      id   = data.aws_kms_alias.s3.arn
      type = "KMS"
    }
  }
  stage {
    name = "Source"

    action {
      name             = "Source"
      category         = "Source"
      owner            = "AWS"
      provider         = "CodeCommit"
      version          = "1"
      output_artifacts = ["source"]

      configuration = {
        RepositoryName = data.aws_codecommit_repository.repo.id
        BranchName     = local.target_branch
      }
    }
  }

  stage {
    name = "Deploy"

    action {
      name             = "Build"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      input_artifacts  = ["source"]
      output_artifacts = ["deployed"]
      version          = "1"

      configuration = {
        ProjectName = aws_codebuild_project.modelbuild_project.name
        EnvironmentVariables = jsonencode(
          [
            {
              name  = "SM_PROJECT_ID"
              value = "${local.sm_project_id}"
              type  = "PLAINTEXT"
            }
        ])
      }
    }
  }
}


