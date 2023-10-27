data "aws_iam_policy_document" "sagemaker_execution_deny_policy" {
  statement {
    effect = "Deny"
    actions = [
      "sagemaker:DeleteModelPackage",
      "sagemaker:UpdateModelPackage",
      "sagemaker:DeleteModelPackageGroup"
    ]
    resources = [
      "arn:aws:sagemaker:${local.aws_region}:${local.account_id}:model-package-group/*",
      "arn:aws:sagemaker:${local.aws_region}:${local.account_id}:model-package/*/*"
    ]
  }
}

data "aws_iam_policy_document" "sagemaker_execution_policy" {
  statement {
    #checkov:skip=CKV_AWS_111:Permissions are meant to be open as its a platform.
    actions = [
      "sagemaker:*App",
      "sagemaker:*Artifact",
      "sagemaker:*AutoMLJob",
      "sagemaker:*CompilationJob",
      "sagemaker:*Context",
      "sagemaker:*DataQualityJobDefinition",
      "sagemaker:*EdgePackagingJob",
      "sagemaker:*Endpoint*",
      "sagemaker:*Experiment",
      "sagemaker:*FeatureGroup",
      "sagemaker:*FlowDefinition",
      "sagemaker:*HyperParameterTuningJob",
      "sagemaker:*InferenceRecommendationsJob",
      "sagemaker:*LineageGroupPolicy",
      "sagemaker:*Model",
      "sagemaker:*ModelBiasJobDefinition",
      "sagemaker:*ModelExplainabilityJobDefinition",
      "sagemaker:*ModelQualityJobDefinition",
      "sagemaker:*MonitoringSchedule",
      "sagemaker:*Pipeline",
      "sagemaker:*ProcessingJob",
      "sagemaker:*TrainingJob",
      "sagemaker:*TransformJob",
      "sagemaker:*Trial*",
      "sagemaker:*PipelineExecution*",
      "sagemaker:QueryLineage",
      "sagemaker:AddAssociation",
      "sagemaker:BatchPutMetric",
      "sagemaker:BatchGetMetrics",
      "sagemaker:CreateAction",
      "sagemaker:AddTags",
      "sagemaker:UpdateEndpointWeightsAndCapacities"
    ]
    resources = [
      "*"
    ]
  }
  statement {
    actions = [
      "sagemaker:Search",
      "sagemaker:Describe*",
      "sagemaker:List*",
      "sagemaker:Get*"
    ]
    resources = ["*"]
  }
  statement {
    actions = [
      "sagemaker:CreateModelPackage",
      "sagemaker:UpdateModelPackage",
      "sagemaker:CreateModelPackageGroup",
      "sagemaker:DeleteModelPackage",
      "sagemaker:DeleteModelPackageGroup",
      "sagemaker:CreateProject"
    ]
    resources = [
      "*"
    ]
  }
}
data "aws_iam_policy_document" "sagemaker_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["sagemaker.amazonaws.com"]
    }
  }
}
data "aws_iam_policy_document" "sagemaker_pass_role_policy" {
  statement {
    actions = [
      "iam:PassRole"
    ]
    resources = [
      "arn:aws:iam::${local.account_id}:role/sagemaker*",
      "arn:aws:iam::${local.account_id}:role/SC*"
    ]
    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["sagemaker.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "sagemaker_s3_policy" {
  statement { # can be limited further but this should be acceptable.
    actions = [
      "s3:List*"
    ]
    resources = [
      "*"
    ]
  }
  statement { # can be limited further but this should be acceptable.
    actions = [
      "s3:Get*",
    ]
    resources = [
      "arn:aws:s3:::sagemaker*/*",
      "arn:aws:s3:::sagemaker*",
      "arn:aws:s3:::mlops*/*",
      "arn:aws:s3:::mlops*"
    ]
  }

  statement {
    actions = [
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:DeleteObjectVersion",
      "s3:AbortMultipartUpload"
    ]
    resources = [
      "arn:aws:s3:::sagemaker*/*",
      "arn:aws:s3:::mlops*/*"
    ]
  }
  statement {
    actions = [
      "iam:CreateServiceLinkedRole"
    ]
    resources = [
      "arn:aws:iam::*:role/aws-service-role/sagemaker.application-autoscaling.amazonaws.com/AWSServiceRoleForApplicationAutoScaling_SageMakerEndpoint"
    ]
    condition {
      test     = "StringLike"
      variable = "iam:AWSServiceName"
      values   = ["sagemaker.application-autoscaling.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "sagemaker_vpc_policy" {
  statement {
    actions = [
      "ec2:DescribeVpcEndpoints",
      "ec2:DescribeDhcpOptions",
      "ec2:DescribeVpcs",
      "ec2:DescribeSubnets",
      "ec2:DescribeSecurityGroups",
      "ec2:DescribeNetworkInterfaces",
      "ec2:DeleteNetworkInterfacePermission",
      "ec2:DeleteNetworkInterface",
      "ec2:CreateNetworkInterfacePermission",
      "ec2:CreateNetworkInterface",
      "ec2:DescribeRouteTables"
    ]
    resources = [
      "*"
    ]
  }
  statement {
    actions = [
      "ec2:CreateNetworkInterface",
      "ec2:CreateNetworkInterfacePermission",
      "ec2:CreateVpcEndpoint",
      "ec2:DeleteNetworkInterface",
      "ec2:DeleteNetworkInterfacePermission"
    ]
    resources = [
      "arn:aws:ec2:${local.aws_region}:${local.account_id}:network-interface/*"
    ]
    condition { #todo: check if this needs tweeking in testing.
      test     = "StringEquals"
      variable = "ec2:AuthorizedService"
      values   = ["sagemaker.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "deny_sagemaker_jobs_outside_vpc" {
  statement {
    effect = "Deny"
    actions = [
      "sagemaker:CreateModel",
      "sagemaker:CreateTrainingJob",
      "sagemaker:CreateProcessingJob"
    ]
    resources = [
      "*"
    ]
    condition {
      test     = "StringNotEquals"
      variable = "sagemaker:VpcSubnets"
      values   = [module.networking.private_subnet_id]
    }
  }
}

data "aws_iam_policy_document" "sagemaker_related_policy" {
  statement {
    #checkov:skip=CKV_AWS_111:Permissions are meant to be open as its a platform.
    actions = [
      "cloudformation:GetTemplateSummary",
      "cloudwatch:DeleteAlarms",
      "cloudwatch:DescribeAlarms",
      "cloudwatch:GetMetricData",
      "cloudwatch:GetMetricStatistics",
      "cloudwatch:ListMetrics",
      "cloudwatch:PutMetricAlarm",
      "cloudwatch:PutMetricData",
      "ecr:BatchCheckLayerAvailability",
      "ecr:BatchGetImage",
      "ecr:CreateRepository",
      "ecr:Describe*",
      "ecr:GetAuthorizationToken",
      "ecr:GetDownloadUrlForLayer",
      "ecr:StartImageScan",
      "elasticfilesystem:DescribeFileSystems",
      "elasticfilesystem:DescribeMountTargets",
      "logs:CreateLogDelivery",
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:DeleteLogDelivery",
      "logs:Describe*",
      "logs:GetLogDelivery",
      "logs:GetLogEvents",
      "logs:ListLogDeliveries",
      "logs:PutLogEvents",
      "logs:PutResourcePolicy",
      "logs:UpdateLogDelivery",
      "servicecatalog:Describe*",
      "servicecatalog:List*",
      "servicecatalog:ScanProvisionedProducts",
      "servicecatalog:SearchProducts",
      "servicecatalog:SearchProvisionedProducts",
      "sns:ListTopics",
      "tag:GetResources",
      "athena:ListDataCatalogs",
      "athena:ListDatabases",
      "athena:ListTableMetadata",
      "athena:GetQueryExecution",
      "athena:GetQueryResults",
      "athena:StartQueryExecution",
      "athena:StopQueryExecution",
      "redshift-data:ExecuteStatement",
      "redshift-data:DescribeStatement",
      "redshift-data:CancelStatement",
      "redshift-data:GetStatementResult",
      "redshift-data:ListSchemas",
      "redshift-data:ListTables"
    ]
    resources = [
      "*"
    ]
  }
  statement { # allow custom resources to be created; limit by naming convetion.
    actions = [
      "ecr:SetRepositoryPolicy",
      "ecr:CompleteLayerUpload",
      "ecr:BatchDeleteImage",
      "ecr:UploadLayerPart",
      "ecr:DeleteRepositoryPolicy",
      "ecr:InitiateLayerUpload",
      "ecr:DeleteRepository",
      "ecr:PutImage"
    ]
    resources = [
      "arn:aws:ecr:*:*:repository/*sagemaker*",
      "arn:aws:ecr:*:*:repository/*sm*"
    ]
  }
  statement {
    actions = [
      "servicecatalog:DescribeProduct",
      "servicecatalog:ProvisionProduct"
    ]
    resources = ["arn:aws:catalog:${local.aws_region}:${local.account_id}:product/*"]
  }
}

#lambda service catalog
data "aws_iam_policy_document" "service_catalog_lambda_policy" {
  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue"
    ]
    resources = [
      "arn:aws:secretsmanager:${local.aws_region}:${local.account_id}:secret:sagemaker/github_pat*",
      "arn:aws:secretsmanager:${local.aws_region}:${local.account_id}:secret:sagemaker/*"
    ]
  }
  statement {
    effect = "Allow"

    actions = [
      "logs:CreateLogGroup",
    ]

    resources = [
      module.clone_repo_lambda.log_arn,
      module.trigger_workflow_lambda.log_arn
    ]
  }


  statement {
    effect = "Allow"
    actions = [
      "logs:PutLogEvents",
      "logs:CreateLogDelivery",
      "logs:CreateLogStream",
    ]
    resources = [
      "${module.clone_repo_lambda.log_arn}:*",
      "${module.trigger_workflow_lambda.log_arn}:*"
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:ListBucket"
    ]
    resources = [
      "arn:aws:s3:::service-catalog-${local.aws_region}-${local.account_id}*/*",
      "arn:aws:s3:::service-catalog-${local.aws_region}-${local.account_id}*"
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "ec2:CreateNetworkInterface"
    ]
    resources = [
      "arn:aws:ec2:${local.aws_region}:${local.account_id}:network-interface/*",
      "arn:aws:ec2:${local.aws_region}:${local.account_id}:security-group/*",
      "arn:aws:ec2:${local.aws_region}:${local.account_id}:subnet/*"
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "ec2:DescribeNetworkInterfaces"
    ]
    resources = [
      "*"
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "ec2:DeleteNetworkInterface"
    ]
    resources = [
      "arn:aws:ec2:${local.aws_region}:${local.account_id}:*/*"
    ]
  }
}





data "aws_iam_policy_document" "service_catalog_lambda_assume_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "sagemaker_launch_service_catalog" {
  statement {
    effect = "Allow"
    actions = [
      "s3:PutEncryptionConfiguration",
      "s3:GetEncryptionConfiguration",
      "lambda:InvokeFunction",
      "events:PutRule",
      "sagemaker:DeleteProject"
    ]
    resources = [
      "arn:aws:sagemaker:${local.aws_region}:${local.account_id}:project/*",
      "arn:aws:lambda:${local.aws_region}:${local.account_id}:function:${module.clone_repo_lambda.lambda_name}",
      "arn:aws:s3:::mlops-*",
      "arn:aws:events:${local.aws_region}:${local.account_id}:rule/*"
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "events:DescribeRule",
      "s3:Put*",
      "s3:CreateBucket",
      "s3:Get*",
      "sagemaker:CreateProject",
      "sagemaker:PutModelPackageGroupPolicy",
      "events:RemoveTargets"
    ]
    resources = [
      "arn:aws:events:${local.aws_region}:${local.account_id}:rule/*",
      "arn:aws:s3:::mlops-mlops-*/*",
      "arn:aws:events:${local.aws_region}:${local.account_id}:rule/*",
      "arn:aws:s3:::mlops-*",
      "arn:aws:s3:::service-catalog*",
      "arn:aws:s3:::service-catalog*/*",
      "arn:aws:sagemaker:${local.aws_region}:${local.account_id}:model-package-group/*",
      "arn:aws:sagemaker:${local.aws_region}:${local.account_id}:project/*"
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "cloudformation:CreateStack",
      "cloudformation:CreateStackInstances",
      "cloudformation:CreateStackSet",
      "cloudformation:DeleteStack",
      "cloudformation:CreateChangeSet",
      "cloudformation:DescribeChangeSet",
      "cloudformation:ExecuteChangeSet",
      "cloudformation:ListChangeSets",
      "cloudformation:DeleteChangeSet",
      "cloudformation:DescribeStackEvents",
      "cloudformation:DescribeStackInstance",
      "cloudformation:ListStackInstances",
      "cloudformation:DescribeStacks",
      "cloudformation:SetStackPolicy",
      "cloudformation:UpdateStack",
      "cloudformation:UpdateStackSet",
      "cloudformation:DescribeStackSetOperation",
      "cloudformation:TagResource",
      "cloudformation:ListStackSetOperations",
      "cloudformation:ListStackSetOperationResults"
    ]
    resources = [
      "arn:aws:cloudformation:${local.aws_region}:${local.account_id}:stack/SC-*",
      "arn:aws:cloudformation:${local.aws_region}:${local.account_id}:stack/StackSet-SC-*",
      "arn:aws:cloudformation:${local.aws_region}:${local.account_id}:changeSet/SC-*",
      "arn:aws:cloudformation:${local.aws_region}:${local.account_id}:stackset/SC-*"

    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "iam:ListRoles",
      "sagemaker:AddTags",
      "sagemaker:ListTags",
      "events:PutPermission",
      "sagemaker:ListCodeRepositories",
      "cloudformation:GetTemplateSummary",
      "cloudformation:ValidateTemplate",
      "servicecatalog:*",
      "s3:Get*"


    ]
    resources = [
      "*"
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "iam:PutRolePolicy",
      "iam:CreatePolicy",
      "iam:AttachRolePolicy",
      "iam:GetRole",
      "iam:GetPolicy",
      "iam:GetRolePolicy",
      "iam:DeleteRole",
      "iam:PassRole",
      "iam:DeleteRolePolicy",
      "iam:DetachRolePolicy",
      "iam:CreateRole",
      "iam:TagRole",
    ]
    resources = [
      "arn:aws:iam::${local.account_id}:policy/*",
      "arn:aws:iam::${local.account_id}:role/SC*"
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "events:PutTargets",
      "lambda:AddPermission",
      "events:ListTargetsByRule"

    ]
    resources = [
      "arn:aws:events:${local.aws_region}:${local.account_id}:rule/*",
      "arn:aws:lambda:${local.aws_region}:${local.account_id}:function:*"
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "iam:PassRole"
    ]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["servicecatalog.amazonaws.com"]
    }
  }
  statement {
    effect = "Allow"
    actions = [
      "sagemaker:CreateCodeRepository",
      "sagemaker:DeleteCodeRepository",
      "sagemaker:DescribeCodeRepository",
      "ssm:GetParameters",
      "ssm:GetParameter",
      "sagemaker:UpdateProject",
      "sagemaker:UpdateCodeRepository",
      "sns:Publish",
      "sagemaker:DescribeModelPackage",
      "sagemaker:UpdateModelPackage",
      "sagemaker:CreateModelPackage",
      "sagemaker:DescribeModelPackageGroup",
      "sagemaker:CreateModelPackageGroup",
      "sagemaker:GetModelPackageGroupPolicy",
      "sagemaker:ListModelPackages"
    ]
    resources = [
      "arn:aws:ssm:${local.aws_region}:${local.account_id}:parameter/*",
      "arn:aws:sagemaker:${local.aws_region}:${local.account_id}:project/*",
      "arn:aws:sagemaker:${local.aws_region}:${local.account_id}:code-repository/*",
      "arn:aws:sns:${local.aws_region}:${local.account_id}:*",
      "arn:aws:sagemaker:${local.aws_region}:${local.account_id}:model-package/*",
      "arn:aws:sagemaker:${local.aws_region}:${local.account_id}:model-package-group/*"
    ]
  }


}
data "aws_iam_policy_document" "servicecatalog_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type = "Service"
      identifiers = [
        "servicecatalog.amazonaws.com",
        "events.amazonaws.com",
        "cloudformation.amazonaws.com",
        "sagemaker.amazonaws.com",
        "lambda.amazonaws.com"
      ]
    }
  }
}

