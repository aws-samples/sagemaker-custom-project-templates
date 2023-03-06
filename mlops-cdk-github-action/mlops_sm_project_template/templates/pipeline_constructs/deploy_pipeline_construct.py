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
    BundlingOptions,
    BundlingOutput,
    Aws,
    aws_codebuild as codebuild,
    aws_codestar as codestar,
    aws_s3 as s3,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_s3_assets as s3_assets,
    aws_cloudformation as cfn,
    aws_secretsmanager as secretsmanager,
    aws_events as events,
    aws_events_targets as targets,
    aws_sqs as sqs,
    aws_ecr as ecr,
    CfnDynamicReference,
    CfnDynamicReferenceService,
)
import aws_cdk as core
from aws_cdk.aws_lambda_python_alpha import PythonFunction
from aws_cdk.custom_resources import Provider
from constructs import Construct


class DeployPipelineConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        project_name: str,
        project_id: str,
        github_user_name: str,
        model_package_group_name: str,
        seed_bucket: str,
        deploy_app_bucket_key: str,
        lambda_function_bucket: str,
        github_action_trigger_lambda_bucket_key: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define resource names
        pipeline_name = f"{project_name}-{construct_id}"

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

        github_deploy_pipeline_role = iam.Role(
            self, 'GithubWebIdentityRoleDeployRepo',
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

        # Add policy to github pipeline deploy role

        github_deploy_pipeline_role.add_to_policy(
            iam.PolicyStatement(
                actions=["sagemaker:ListModelPackages"],
                resources=[
                    f"arn:{Aws.PARTITION}:sagemaker:{Aws.REGION}:{Aws.ACCOUNT_ID}:model-package-group/{project_name}-{project_id}*",
                    f"arn:{Aws.PARTITION}:sagemaker:{Aws.REGION}:{Aws.ACCOUNT_ID}:model-package/{project_name}-{project_id}/*",
                ],
            )
        )

        github_deploy_pipeline_role.add_to_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter"],
                resources=[
                    f"arn:{Aws.PARTITION}:ssm:{Aws.REGION}:{Aws.ACCOUNT_ID}:parameter/*",
                ],
            )
        )

        github_deploy_pipeline_role.add_to_policy(
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
        )

        github_deploy_pipeline_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "iam:PassRole",
                    "sts:AssumeRole",
                ],
                effect=iam.Effect.ALLOW,
                resources=[f"arn:aws:iam::{Aws.ACCOUNT_ID}:role/cdk-hnb659fds-*-{Aws.ACCOUNT_ID}-{Aws.REGION}"],
            ),
        )

        github_deploy_pipeline_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=["*"],
            ),
        )

        github_deploy_pipeline_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "cloudwatch:PutMetricData",
                ],
                resources=["*"],
            ),
        )

        # Push deploy seed code to GitHub repo and create secrets in GitHub secrets
        github_secret_create_lambda_ecr_repo_name = CfnDynamicReference(
            CfnDynamicReferenceService.SSM, "/mlops/ecr/repo/github-secret-create-lambada").to_string()
        github_secret_create_lambda_ecr_repo_tag = CfnDynamicReference(
            CfnDynamicReferenceService.SSM, "/mlops/ecr/repo/github-secret-create-lambada-ecr-tag").to_string()
        repo = ecr.Repository.from_repository_name(self, "ECRRepoNameDeploy",
                                                   repository_name=github_secret_create_lambda_ecr_repo_name)
        github_store_secret_lambda = lambda_.DockerImageFunction(
            scope=self,
            id="DockerLambdaForSecretNRepo",
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

        build_code_repo = s3.Bucket.from_bucket_name(self, "DeployCodeBucketByName", seed_bucket)
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
            id="LambdaForGitCodeSecretCreate",
            service_token=github_store_secret_lambda.function_arn,
            removal_policy=core.RemovalPolicy.DESTROY,
            properties={
               "SAGEMAKER_PROJECT_NAME": project_name,
               "SAGEMAKER_PROJECT_ID": project_id,
               "MODEL_PACKAGE_GROUP_NAME": model_package_group_name,
               "ACCOUNT_AWS_REGION": Aws.REGION,
               "SAGEMAKER_PIPELINE_NAME": pipeline_name,
               "GITHUB_REPO_NAME": f"{project_name}-{construct_id}",
               "PIPELINE_EXECUTION_IAM_ROLE": github_deploy_pipeline_role.role_arn,
               "S3_BUCKET_NAME": seed_bucket,
               "S3_OBJECT_KEY": deploy_app_bucket_key,
            }
        )


        """
        Create the Custom Resource to seed code and env variable to github 
        """
        lambda_function_bucket_obj = s3.Bucket.from_bucket_name(self, "BucketByName", lambda_function_bucket)
        fn_seed = lambda_.Function(self, "model-approval-trigger-github-repo-function",
                                   runtime=lambda_.Runtime.PYTHON_3_9,
                                   handler="index.handler",
                                   code=lambda_.Code.from_bucket(bucket=lambda_function_bucket_obj,
                                                                 key=github_action_trigger_lambda_bucket_key),
                                   environment={
                                       "SAGEMAKER_PROJECT_NAME": project_name,
                                       "SAGEMAKER_PROJECT_ID": project_id,
                                       "MODEL_PACKAGE_GROUP_NAME": model_package_group_name,
                                       "ACCOUNT_AWS_REGION": Aws.REGION,
                                       "SAGEMAKER_PIPELINE_NAME": pipeline_name,
                                       "GITHUB_REPO_NAME": f"{project_name}-{construct_id}",
                                   })

        queue = sqs.Queue(self, f"ModelApprovalEventFailedQueue")

        fn_seed.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue",
                    "sqs:*"
                ],
                resources=[f"arn:aws:secretsmanager:{Aws.REGION}:{Aws.ACCOUNT_ID}:secret:GithubSecret-{project_name}-*",
                           queue.queue_arn]
            ),
        )

        # CloudWatch rule to trigger model pipeline when a status change event happens to the model package group
        model_event_rule = events.Rule(
            self,
            "ModelApprovalEventRule",
            enabled=True,
            event_pattern=events.EventPattern(
                source=["aws.sagemaker"],
                detail_type=["SageMaker Model Package State Change"],
                detail={
                    "ModelPackageGroupName": [model_package_group_name],
                    "ModelApprovalStatus": ["Approved"],
                },
            ),
            targets=[targets.LambdaFunction(fn_seed,
                                            dead_letter_queue=queue,  # Optional: add a dead letter queue
                                            max_event_age=core.Duration.hours(2),
                                            # Optional: set the maxEventAge retry policy
                                            retry_attempts=2
                                            )],
        )