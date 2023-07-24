from aws_cdk import (
    Aws,
    aws_s3 as s3,
    aws_iam as iam,
    aws_codecommit as codecommit,
    aws_codebuild as codebuild,
    aws_codepipeline_actions as codepipeline_actions,
    aws_codepipeline as codepipeline,
)

from constructs import Construct


class BuildPipeline(Construct):
    def __init__(
        self,
        scope: Construct,
        project_name: str,
        project_id: str,
        construct_id: str,
        s3_artifact: s3.IBucket,
        build_app_repository: codecommit.IRepository,
        stg_account: str,
        prod_account: str,
        dev_model_package_group_name: str,
        stg_model_package_group_name: str,
        prod_model_package_group_name: str,
    ) -> None:
        super().__init__(scope, construct_id)

        codebuild_role = iam.Role(
            self,
            "BuildPipelineCodeBuildRole",
            assumed_by=iam.ServicePrincipal("codebuild.amazonaws.com"),
            path="/service-role/",
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
                            "s3:Put*",
                            "s3:Create*",
                        ],
                        resources=[
                            s3_artifact.bucket_arn,
                            f"{s3_artifact.bucket_arn}/*",
                            "arn:aws:s3:::sagemaker-*",
                        ],
                    ),
                    iam.PolicyStatement(
                        actions=["iam:PassRole"],
                        resources=[sagemaker_execution_role.role_arn],
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
        sagemaker_policy.attach_to_role(codebuild_role)

        pipeline_name = f"build-{project_name}-{construct_id}"
        pipeline_description = f"{project_name} Model Build Pipeline"

        build_pipeline = codepipeline.Pipeline(
            self, "Pipeline", pipeline_name=pipeline_name, artifact_bucket=s3_artifact
        )

        source_artifact = codepipeline.Artifact(artifact_name="GitSource")
        source_stage = build_pipeline.add_stage(stage_name="Source")
        source_stage.add_action(
            codepipeline_actions.CodeCommitSourceAction(
                action_name="Source",
                output=source_artifact,
                repository=build_app_repository,
                branch="main",
            )
        )

        # add a build stage
        dev_sm_pipeline_build = codebuild.PipelineProject(
            self,
            "DevSMPipelineBuild",
            project_name=f"{project_name}-{construct_id}-dev",
            role=codebuild_role,
            build_spec=codebuild.BuildSpec.from_source_filename("buildspec.yml"),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_5_0,
                environment_variables={
                    "SAGEMAKER_PROJECT_NAME": codebuild.BuildEnvironmentVariable(
                        value=project_name
                    ),
                    "SAGEMAKER_PROJECT_ID": codebuild.BuildEnvironmentVariable(
                        value=project_id
                    ),
                    "MODEL_PACKAGE_GROUP_NAME": codebuild.BuildEnvironmentVariable(
                        value=dev_model_package_group_name
                    ),
                    "AWS_REGION": codebuild.BuildEnvironmentVariable(value=Aws.REGION),
                    "SAGEMAKER_PIPELINE_NAME": codebuild.BuildEnvironmentVariable(
                        value=pipeline_name,
                    ),
                    "SAGEMAKER_PIPELINE_DESCRIPTION": codebuild.BuildEnvironmentVariable(
                        value=pipeline_description,
                    ),
                    "SAGEMAKER_PIPELINE_ROLE_ARN": codebuild.BuildEnvironmentVariable(
                        value=sagemaker_execution_role.role_arn,
                    ),
                    "ARTIFACT_BUCKET": codebuild.BuildEnvironmentVariable(
                        value=s3_artifact.bucket_name
                    ),
                    "ARTIFACT_BUCKET_KMS_ID": codebuild.BuildEnvironmentVariable(
                        value=s3_artifact.encryption_key.key_arn
                    ),
                },
            ),
        )
        dev_build_stage = build_pipeline.add_stage(stage_name="DevBuild")

        dev_build_stage.add_action(
            codepipeline_actions.CodeBuildAction(
                action_name="SMPipeline",
                input=source_artifact,
                project=dev_sm_pipeline_build,
                run_order=1,
            )
        )
        dev_build_stage.add_action(
            codepipeline_actions.ManualApprovalAction(
                action_name="Approve_Stg",
                run_order=2,
                additional_information="Approving deployment for staging",
            ),
        )

        # register model step in stg and prod will need cross account access to write to tooling
        stg_sm_pipeline_build = codebuild.PipelineProject(
            self,
            "StgSMPipelineBuild",
            project_name=f"{project_name}-{construct_id}-stg",
            role=codebuild_role, 
            build_spec=codebuild.BuildSpec.from_source_filename(
                "cross_acc_buildspec.yml"
            ),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_5_0,
                environment_variables={
                    "ACCOUNT_ID": codebuild.BuildEnvironmentVariable(value=stg_account),
                    "SAGEMAKER_PROJECT_NAME": codebuild.BuildEnvironmentVariable(
                        value=project_name
                    ),
                    "SAGEMAKER_PROJECT_ID": codebuild.BuildEnvironmentVariable(
                        value=project_id
                    ),
                    "MODEL_PACKAGE_GROUP_NAME": codebuild.BuildEnvironmentVariable(
                        value=f"arn:aws:sagemaker:{Aws.REGION}:{Aws.ACCOUNT_ID}:model-package-group/{stg_model_package_group_name}"
                    ),
                    "AWS_REGION": codebuild.BuildEnvironmentVariable(value=Aws.REGION),
                    "SAGEMAKER_PIPELINE_NAME": codebuild.BuildEnvironmentVariable(
                        value=pipeline_name,
                    ),
                    "SAGEMAKER_PIPELINE_DESCRIPTION": codebuild.BuildEnvironmentVariable(
                        value=pipeline_description,
                    ),
                    "SAGEMAKER_PIPELINE_ROLE_ARN": codebuild.BuildEnvironmentVariable(
                        value=sagemaker_execution_role.role_arn,
                    ),
                    "ARTIFACT_BUCKET": codebuild.BuildEnvironmentVariable(
                        value=s3_artifact.bucket_name
                    ),
                    "ARTIFACT_BUCKET_KMS_ID": codebuild.BuildEnvironmentVariable(
                        value=s3_artifact.encryption_key.key_arn
                    ),
                },
            ),
        )
        stg_sm_pipeline_build.add_to_role_policy(
            iam.PolicyStatement(
                actions=["sts:Assume"], resources=["*"], effect=iam.Effect.ALLOW
            )
        )

        stg_build_stage = build_pipeline.add_stage(stage_name="StgBuild")
        stg_build_stage.add_action(
            codepipeline_actions.CodeBuildAction(
                action_name="SMPipeline",
                input=source_artifact,
                project=stg_sm_pipeline_build,
                run_order=1,
            )
        )
        stg_build_stage.add_action(
            codepipeline_actions.ManualApprovalAction(
                action_name="Approve_Prod",
                run_order=2,
                additional_information="Approving deployment for production",
            ),
        )

        # prod step
        prod_sm_pipeline_build = codebuild.PipelineProject(
            self,
            "ProdSMPipelineBuild",
            project_name=f"{project_name}-{construct_id}-prod",
            role=codebuild_role,
            build_spec=codebuild.BuildSpec.from_source_filename(
                "cross_acc_buildspec.yml"
            ),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_5_0,
                environment_variables={
                    "ACCOUNT_ID": codebuild.BuildEnvironmentVariable(
                        value=prod_account
                    ),
                    "SAGEMAKER_PROJECT_NAME": codebuild.BuildEnvironmentVariable(
                        value=project_name
                    ),
                    "SAGEMAKER_PROJECT_ID": codebuild.BuildEnvironmentVariable(
                        value=project_id
                    ),
                    "MODEL_PACKAGE_GROUP_NAME": codebuild.BuildEnvironmentVariable(
                        value=f"arn:aws:sagemaker:{Aws.REGION}:{Aws.ACCOUNT_ID}:model-package-group/{prod_model_package_group_name}"
                    ),
                    "AWS_REGION": codebuild.BuildEnvironmentVariable(value=Aws.REGION),
                    "SAGEMAKER_PIPELINE_NAME": codebuild.BuildEnvironmentVariable(
                        value=pipeline_name,
                    ),
                    "SAGEMAKER_PIPELINE_DESCRIPTION": codebuild.BuildEnvironmentVariable(
                        value=pipeline_description,
                    ),
                    "SAGEMAKER_PIPELINE_ROLE_ARN": codebuild.BuildEnvironmentVariable(
                        value=sagemaker_execution_role.role_arn,
                    ),
                    "ARTIFACT_BUCKET": codebuild.BuildEnvironmentVariable(
                        value=s3_artifact.bucket_name
                    ),
                    "ARTIFACT_BUCKET_KMS_ID": codebuild.BuildEnvironmentVariable(
                        value=s3_artifact.encryption_key.key_arn
                    ),
                },
            ),
        )
        prod_sm_pipeline_build.add_to_role_policy(
            iam.PolicyStatement(
                actions=["sts:AssumeRole"], resources=["*"], effect=iam.Effect.ALLOW
            )
        )

        prod_build_stage = build_pipeline.add_stage(stage_name="ProdBuild")
        prod_build_stage.add_action(
            codepipeline_actions.CodeBuildAction(
                action_name="SMPipeline",
                input=source_artifact,
                project=prod_sm_pipeline_build,
            )
        )
