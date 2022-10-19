data "aws_iam_policy_document" "codebuild_assume_policy" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["codebuild.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "codebuild_role" {
  name               = "${local.prefix}-${local.sm_project_name}-codebuild-modeldeploy-role"
  assume_role_policy = data.aws_iam_policy_document.codebuild_assume_policy.json
}

# TODO: SCOPE THIS DOWN!!!!!!!!!!!!!!!!!!!!!
resource "aws_iam_role_policy_attachment" "power_user" {
  role       = aws_iam_role.codebuild_role.id
  policy_arn = "arn:aws:iam::aws:policy/PowerUserAccess"
}

resource "aws_iam_policy" "manage_roles" {
  description = "pass_role_to_sm_pipelines for SM Pipelines for ${local.sm_project_name}"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "iam:GetRole",
        "iam:CreatePolicy",
        "iam:GetPolicy",
        "iam:GetPolicyVersion",
        "iam:ListPolicyVersions",
        "iam:ListRolePolicies",
        "iam:ListAttachedRolePolicies",
        "iam:GetRolePolicy",
        "iam:GetPolicy",
        "iam:CreateRole",
        "iam:CreatePolicyVersion"
      ],
      "Effect": "Allow",
      "Resource": [
          "${aws_iam_role.start_code_pipeline_role.arn}",
          "${aws_iam_role.codepipeline_role.arn}",
          "${aws_iam_role.codebuild_role.arn}",
          "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/terraform-*"
      ]
    }
  ]
}
EOF
}


resource "aws_iam_role_policy_attachment" "attach_manage_roles_to_sm_pipelines" {
  role       = aws_iam_role.codebuild_role.name
  policy_arn = aws_iam_policy.manage_roles.arn
}

resource "aws_iam_policy" "pass_sm_execution_role" {
  description = "pass_role_to_sm_pipelines for SM Pipelines for ${local.sm_project_id}"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "iam:PassRole"
      ],
      "Effect": "Allow",
      "Resource": "${local.sagemaker_execution_role}"
    }
  ]
}
EOF
}


resource "aws_iam_role_policy_attachment" "attach_pass_sm_execution_role" {
  role       = aws_iam_role.codebuild_role.name
  policy_arn = aws_iam_policy.pass_sm_execution_role.arn
}



resource "aws_codebuild_project" "modeldeploy_project" {
  name          = "${local.prefix}-${local.sm_project_name}-modeldeploy"
  description   = "The CodeBuild project for ${data.aws_codecommit_repository.repo.id}"
  service_role  = aws_iam_role.codebuild_role.arn
  build_timeout = local.build_timeout

  artifacts {
    type = "CODEPIPELINE"
  }

  cache {
    type  = "LOCAL"
    modes = ["LOCAL_DOCKER_LAYER_CACHE"]
  }

  environment {
    compute_type    = local.build_compute_type
    image           = local.build_image
    type            = "LINUX_CONTAINER"
    privileged_mode = local.build_privileged_override
    environment_variable {
      name  = "PREFIX"
      value = local.prefix
    }

    environment_variable {
      name  = "SAGEMAKER_PROJECT_ID"
      value = local.sm_project_id
    }

    environment_variable {
      name  = "SAGEMAKER_PROJECT_NAME"
      value = local.sm_project_name
    }

    environment_variable {
      name  = "ARTIFACT_BUCKET"
      value = local.artifact_bucket_name
    }

    environment_variable {
      name  = "MODEL_PACKAGE_GROUP_NAME"
      value = local.model_package_group_name
    }

    environment_variable {
      name  = "ARTIFACT_BUCKET_KMS_ID"
      value = data.aws_kms_alias.s3.target_key_arn
    }

    environment_variable {
      name  = "SAGEMAKER_EXECUTION_ROLE"
      value = local.sagemaker_execution_role
    }
  }

  source {
    type = "CODEPIPELINE"
  }
}