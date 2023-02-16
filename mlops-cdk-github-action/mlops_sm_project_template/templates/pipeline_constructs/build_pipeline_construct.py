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
from os import path

from aws_cdk import (
    BundlingOptions,
    BundlingOutput,
    Aws,
    aws_codebuild as codebuild,
    aws_codestar as codestar,
    aws_s3 as s3,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_ecr as ecr,
    aws_s3_assets as s3_assets,
    aws_cloudformation as cfn,
    aws_secretsmanager as secretsmanager,
    aws_events as events,
    aws_events_targets as targets,
    aws_sqs as sqs,
    CfnDynamicReference,
    CfnDynamicReferenceService,
)
import aws_cdk as core
from aws_cdk.aws_lambda_python_alpha import PythonFunction
from aws_cdk.custom_resources import Provider
from constructs import Construct


class BuildPipelineConstruct(Construct):
    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            project_name: str,
            project_id: str,
            github_user_name: str,
            s3_artifact: s3.IBucket,
            model_package_group_name: str,
            repo_s3_bucket_name: str,
            repo_s3_object_key: str,
            **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define resource names
        pipeline_name = f"{project_name}-{construct_id}"
        pipeline_description = f"{project_name} Model Build Pipeline"

        # Create web-identity role for the deployment repository
        provider = iam.OpenIdConnectProvider.from_open_id_connect_provider_arn(self, 'git-hub-provider',
                                                                               open_id_connect_provider_arn=f"arn:aws:iam::{Aws.ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com")
        if not provider:
            provider = iam.OpenIdConnectProvider(
                self, 'provider',
                url='https://token.actions.githubusercontent.com',
                client_ids=[
                    'sts.amazonaws.com'
                ]
            )
        github_pipeline_role = iam.Role(
            self, 'GithubWebIdentityRoleBuildRepo',
            assumed_by=iam.WebIdentityPrincipal(
                provider.open_id_connect_provider_arn
            ).with_conditions(
                {
                    'StringLike': {
                        'token.actions.githubusercontent.com:sub': f'repo:{github_user_name}/{project_name}-{construct_id}:*'
                    }
                }
            )
        )

        sagemaker_execution_role = iam.Role(
            self,
            "SageMakerExecutionRole",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            path="/service-role/",
        )

        # Create a policy statement for SM and ECR pull
        sagemaker_policy = iam.Policy(
            self,
            "SageMakerPolicy",
            document=iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        actions=[
                            "logs:CreateLogGroup",
                            "logs:CreateLogStream",
                            "logs:PutLogEvents",
                        ],
                        resources=["*"],
                    ),
                    iam.PolicyStatement(
                        actions=["sagemaker:*"],
                        not_resources=[
                            "arn:aws:sagemaker:*:*:domain/*",
                            "arn:aws:sagemaker:*:*:user-profile/*",
                            "arn:aws:sagemaker:*:*:app/*",
                            "arn:aws:sagemaker:*:*:flow-definition/*",
                        ],
                    ),
                    iam.PolicyStatement(
                        actions=[
                            "ecr:BatchCheckLayerAvailability",
                            "ecr:BatchGetImage",
                            "ecr:Describe*",
                            "ecr:GetAuthorizationToken",
                            "ecr:GetDownloadUrlForLayer",
                        ],
                        resources=["*"],
                    ),
                    iam.PolicyStatement(
                        actions=[
                            "cloudwatch:PutMetricData",
                        ],
                        resources=["*"],
                    ),
                    iam.PolicyStatement(
                        actions=[
                            "s3:AbortMultipartUpload",
                            "s3:DeleteObject",
                            "s3:GetBucket*",
                            "s3:GetObject*",
                            "s3:List*",
                            "s3:PutObject*",
                            "s3:Create*",
                        ],
                        resources=[s3_artifact.bucket_arn, f"{s3_artifact.bucket_arn}/*", "arn:aws:s3:::sagemaker-*"],
                    ),
                    iam.PolicyStatement(
                        actions=["iam:PassRole"],
                        resources=[f"{sagemaker_execution_role.role_arn}*"],
                    ),
                    iam.PolicyStatement(
                        actions=[
                            "kms:Encrypt",
                            "kms:ReEncrypt*",
                            "kms:GenerateDataKey*",
                            "kms:Decrypt",
                            "kms:DescribeKey",
                        ],
                        effect=iam.Effect.ALLOW,
                        resources=[f"arn:aws:kms:{Aws.REGION}:{Aws.ACCOUNT_ID}:key/*"],
                    ),
                ]
            ),
        )

        sagemaker_policy.attach_to_role(sagemaker_execution_role)
        sagemaker_policy.attach_to_role(github_pipeline_role)

        # Push deploy seed code to GitHub repo and create secrets in GitHub secrets
        github_secret_create_lambda_ecr_repo_name = CfnDynamicReference(
            CfnDynamicReferenceService.SSM, "/mlops/ecr/repo/github-secret-create-lambada").to_string()
        github_secret_create_lambda_ecr_repo_tag = CfnDynamicReference(
            CfnDynamicReferenceService.SSM, "/mlops/ecr/repo/github-secret-create-lambada-ecr-tag").to_string()
        repo = ecr.Repository.from_repository_name(self, "ECRRepoName",
                                                         repository_name=github_secret_create_lambda_ecr_repo_name)
        github_store_secret_lambda = lambda_.DockerImageFunction(
            scope=self,
            id="LambdaDockerForGitHubSecretUpdate",
            # a docker image on deployment
            code=lambda_.DockerImageCode.from_ecr(repo, tag=github_secret_create_lambda_ecr_repo_tag),
            timeout=core.Duration.seconds(120)
        )

        github_store_secret_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue"
                ],
                resources=[f"arn:aws:secretsmanager:{Aws.REGION}:{Aws.ACCOUNT_ID}:secret:GithubSecret-{project_name}-*"]
            ),
        )

        build_code_repo = s3.Bucket.from_bucket_name(self, "BuildCodeBucketByName", repo_s3_bucket_name)
        github_store_secret_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:*"
                ],
                resources=[build_code_repo.bucket_arn, f"{build_code_repo.bucket_arn}/*"]
            ),
        )

        invokeLambdaForSecretCreate = core.CustomResource(
            scope=self,
            id="InvokeLambdaForCodeAndSecretCreate",
            service_token=github_store_secret_lambda.function_arn,
            removal_policy=core.RemovalPolicy.DESTROY,
            properties={
                "SAGEMAKER_PROJECT_NAME": project_name,
                "SAGEMAKER_PROJECT_ID": project_id,
                "MODEL_PACKAGE_GROUP_NAME": model_package_group_name,
                "ACCOUNT_AWS_REGION": Aws.REGION,
                "SAGEMAKER_PIPELINE_NAME": pipeline_name,
                "SAGEMAKER_PIPELINE_DESCRIPTION": pipeline_description,
                "SAGEMAKER_PIPELINE_ROLE_ARN": sagemaker_execution_role.role_arn,
                "ARTIFACT_BUCKET": s3_artifact.bucket_name,
                "ARTIFACT_BUCKET_KMS_ID": s3_artifact.encryption_key.key_id,
                "GITHUB_REPO_NAME": f"{project_name}-{construct_id}",
                "PIPELINE_EXECUTION_IAM_ROLE": github_pipeline_role.role_arn,
                "S3_BUCKET_NAME": repo_s3_bucket_name,
                "S3_OBJECT_KEY": repo_s3_object_key,
            }
        )


