# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# SPDX-License-Identifier: MIT-0
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from aws_cdk import (
    Aws,
    CfnDynamicReference,
    CfnDynamicReferenceService,
    Stack,
    Tags,
    aws_s3 as s3,
    aws_iam as iam,
    aws_kms as kms,
    aws_sagemaker as sagemaker,
    aws_secretsmanager as secretsmanager,
    aws_lambda as lambda_,
)

import aws_cdk

from constructs import Construct

from mlops_sm_project_template.templates.pipeline_constructs.build_pipeline_construct import (
    BuildPipelineConstruct,
)
from mlops_sm_project_template.templates.pipeline_constructs.deploy_pipeline_construct import (
    DeployPipelineConstruct,
)


class MLOpsStack(Stack):
    DESCRIPTION: str = "This template includes a model building pipeline that includes a workflow to pre-process, " \
                       "train, evaluate and register a model by using the GitHub Action as the CI/CD tool"
    TEMPLATE_NAME: str = "MLOps with GitHub Action template for real-time deployment"

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define required parameters
        project_name = aws_cdk.CfnParameter(
            self,
            "SageMakerProjectName",
            type="String",
            description="The name of the SageMaker project.",
            min_length=1,
            max_length=32,
        ).value_as_string

        project_id = aws_cdk.CfnParameter(
            self,
            "SageMakerProjectId",
            type="String",
            min_length=1,
            max_length=16,
            description="Service generated Id of the project.",
        ).value_as_string

        github_user_name = aws_cdk.CfnParameter(
            self,
            "GithubUserName",
            type="String",
            min_length=1,
            max_length=100,
            description="The GitHub user name for the owner of the GitHub repository to be created.",
        ).value_as_string

        repository_access_token = aws_cdk.CfnParameter(
            self,
            "GithubAccessToken",
            type="String",
            min_length=1,
            max_length=500,
            no_echo=True,
            description="The GitHub user’s personal access token for the GitHub repository.",
        ).value_as_string

        Tags.of(self).add("sagemaker:project-id", project_id)
        Tags.of(self).add("sagemaker:project-name", project_name)

        # Create a GitHub secret

        gh_secret = secretsmanager.Secret(
            self,
            "GithubAccessTokenSecretCreate",
            secret_name=f"GithubSecret-{project_name}",
            secret_string_value=aws_cdk.SecretValue.unsafe_plain_text('{"owner": "'+github_user_name+'", "access_key": "'+repository_access_token+'"}'),
            removal_policy=aws_cdk.RemovalPolicy.DESTROY,
        )

        # DEV account access to secret in the SM
        gh_secret.add_to_resource_policy(
            iam.PolicyStatement(
                sid="AddDevSecretManagerPermissions",
                actions=["secretsmanager:*"],
                resources=[
                    gh_secret.secret_arn,
                ],
                principals=[
                    iam.ArnPrincipal(f"arn:aws:iam::{Aws.ACCOUNT_ID}:root"),
                ],
            )
        )

        # create kms key to be used by the assets bucket
        kms_key = kms.Key(
            self,
            "ArtifactsBucketKMSKey",
            description="key used for encryption of data in Amazon S3",
            enable_key_rotation=True,
            policy=iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        actions=["kms:*"],
                        effect=iam.Effect.ALLOW,
                        resources=["*"],
                        principals=[iam.AccountRootPrincipal()],
                    )
                ]
            ),
        )

        s3_artifact = s3.Bucket(
            self,
            "S3Artifact",
            bucket_name=f"mlops-{project_name}-{project_id}-{Aws.REGION}",
            encryption_key=kms_key,
            versioned=True,
            removal_policy=aws_cdk.RemovalPolicy.DESTROY,
        )

        # Block insecure requests to the bucket
        s3_artifact.add_to_resource_policy(
            iam.PolicyStatement(
                sid="AllowSSLRequestsOnly",
                actions=["s3:*"],
                effect=iam.Effect.DENY,
                resources=[
                    s3_artifact.bucket_arn,
                    s3_artifact.arn_for_objects(key_pattern="*"),
                ],
                conditions={"Bool": {"aws:SecureTransport": "false"}},
                principals=[iam.AnyPrincipal()],
            )
        )

        # DEV account access to objects in the bucket
        s3_artifact.add_to_resource_policy(
            iam.PolicyStatement(
                sid="AddDevPermissions",
                actions=["s3:*"],
                resources=[
                    s3_artifact.arn_for_objects(key_pattern="*"),
                    s3_artifact.bucket_arn,
                ],
                principals=[
                    iam.ArnPrincipal(f"arn:aws:iam::{Aws.ACCOUNT_ID}:root"),
                ],
            )
        )

        model_package_group_name = f"{project_name}-{project_id}"

        # cross account model registry resource policy
        model_package_group_policy = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    sid="ModelPackageGroup",
                    actions=[
                        "sagemaker:DescribeModelPackageGroup",
                    ],
                    resources=[
                        f"arn:aws:sagemaker:{Aws.REGION}:{Aws.ACCOUNT_ID}:model-package-group/{model_package_group_name}"
                    ],
                    principals=[
                        iam.ArnPrincipal(f"arn:aws:iam::{Aws.ACCOUNT_ID}:root"),
                    ],
                ),
                iam.PolicyStatement(
                    sid="ModelPackage",
                    actions=[
                        "sagemaker:DescribeModelPackage",
                        "sagemaker:ListModelPackages",
                        "sagemaker:UpdateModelPackage",
                        "sagemaker:CreateModel",
                    ],
                    resources=[
                        f"arn:aws:sagemaker:{Aws.REGION}:{Aws.ACCOUNT_ID}:model-package/{model_package_group_name}/*"
                    ],
                    principals=[
                        iam.ArnPrincipal(f"arn:aws:iam::{Aws.ACCOUNT_ID}:root"),
                    ],
                ),
            ]
        ).to_json()

        model_package_group = sagemaker.CfnModelPackageGroup(
            self,
            "ModelPackageGroup",
            model_package_group_name=model_package_group_name,
            model_package_group_description=f"Model Package Group for {project_name}",
            model_package_group_policy=model_package_group_policy,
            tags=[
                aws_cdk.CfnTag(key="sagemaker:project-id", value=project_id),
                aws_cdk.CfnTag(key="sagemaker:project-name", value=project_name),
            ],
        )

        seed_bucket = CfnDynamicReference(CfnDynamicReferenceService.SSM, "/mlops/code/seed_bucket").to_string()
        build_app_bucket_key = CfnDynamicReference(CfnDynamicReferenceService.SSM, "/mlops/code/build").to_string()
        deploy_app_bucket_key = CfnDynamicReference(CfnDynamicReferenceService.SSM, "/mlops/code/deploy").to_string()
        lambda_function_bucket = CfnDynamicReference(CfnDynamicReferenceService.SSM,
                                                     "/mlops/lambda_function/bucket").to_string()
        github_action_trigger_lambda_bucket_key = CfnDynamicReference(CfnDynamicReferenceService.SSM,
                                                                      "/mlops/lambda/github-action-trigger").to_string()

        BuildPipelineConstruct(
            self,
            "build",
            project_name,
            project_id,
            github_user_name,
            s3_artifact,
            model_package_group_name,
            seed_bucket,
            build_app_bucket_key
        )

        DeployPipelineConstruct(
            self,
            "deploy",
            project_name,
            project_id,
            github_user_name,
            model_package_group_name,
            seed_bucket,
            deploy_app_bucket_key,
            lambda_function_bucket,
            github_action_trigger_lambda_bucket_key
        )
