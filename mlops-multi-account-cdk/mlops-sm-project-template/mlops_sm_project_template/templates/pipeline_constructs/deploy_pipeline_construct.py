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
    CfnCapabilities,
    aws_codecommit as codecommit,
    aws_codebuild as codebuild,
    aws_codepipeline_actions as codepipeline_actions,
    aws_codepipeline as codepipeline,
    aws_events as events,
    aws_events_targets as targets,
    aws_s3 as s3,
    aws_iam as iam,
)
import aws_cdk
from constructs import Construct


class DeployPipelineConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        project_name: str,
        project_id: str,
        pipeline_artifact_bucket: s3.IBucket,
        model_package_group_name: str,
        repo_s3_bucket_name: str,
        repo_s3_object_key: str,
        preprod_account: int,
        prod_account: int,
        deployment_region: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define resource names
        pipeline_name = f"{project_name}-{construct_id}"

        # Create source repo from seed bucket/key
        deploy_app_cfnrepository = codecommit.CfnRepository(
            self,
            "BuildAppCodeRepo",
            repository_name=f"{project_name}-{construct_id}",
            code=codecommit.CfnRepository.CodeProperty(
                s3=codecommit.CfnRepository.S3Property(
                    bucket=repo_s3_bucket_name,
                    key=repo_s3_object_key,
                    object_version=None,
                ),
                branch_name="main",
            ),
            tags=[
                aws_cdk.CfnTag(key="sagemaker:project-id", value=project_id),
                aws_cdk.CfnTag(key="sagemaker:project-name", value=project_name),
            ],
        )

        # Reference the newly created repository
        deploy_app_repository = codecommit.Repository.from_repository_name(
            self, "ImportedDeployRepo", deploy_app_cfnrepository.attr_name
        )

        cdk_synth_build_role = iam.Role(
            self,
            "CodeBuildRole",
            assumed_by=iam.ServicePrincipal("codebuild.amazonaws.com"),
            path="/service-role/",
        )

        cdk_synth_build_role.add_to_policy(
            iam.PolicyStatement(
                actions=["sagemaker:ListModelPackages"],
                resources=[
                    f"arn:{Aws.PARTITION}:sagemaker:{Aws.REGION}:{Aws.ACCOUNT_ID}:model-package-group/{project_name}-{project_id}*",
                    f"arn:{Aws.PARTITION}:sagemaker:{Aws.REGION}:{Aws.ACCOUNT_ID}:model-package/{project_name}-{project_id}/*",
                ],
            )
        )
        cdk_synth_build_role.add_to_policy(
            iam.PolicyStatement(
                actions=["sagemaker:*"],
                resources=[
                    "*"
                ],
            )
        )

        cdk_synth_build_role.add_to_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter"],
                resources=[
                    f"arn:{Aws.PARTITION}:ssm:{Aws.REGION}:{Aws.ACCOUNT_ID}:parameter/*",
                ],
            )
        )

        cdk_synth_build_role.add_to_policy(
            iam.PolicyStatement(
                actions=["sts:AssumeRole"],
                resources=[
                    f'arn:aws:iam::{Aws.ACCOUNT_ID}:role/cdk-hnb659fds-file-publishing-role-{Aws.ACCOUNT_ID}-{Aws.REGION}',
                    f'arn:aws:iam::{preprod_account}:role/cdk-hnb659fds-file-publishing-role-{preprod_account}-{Aws.REGION}',
                    f'arn:aws:iam::{prod_account}:role/cdk-hnb659fds-file-publishing-role-{prod_account}-{Aws.REGION}',
                ],
            )
        )

        cdk_synth_build_role.add_to_policy(
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
        env = codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_5_0,
                privileged=True,
                environment_variables={
                    "MODEL_PACKAGE_GROUP_NAME": codebuild.BuildEnvironmentVariable(value=model_package_group_name),
                    "PROJECT_ID": codebuild.BuildEnvironmentVariable(value=project_id),
                    "PROJECT_NAME": codebuild.BuildEnvironmentVariable(value=project_name),
                },
            )

        cdk_synth_build = codebuild.PipelineProject(
            self,
            "CDKSynthBuild",
            role=cdk_synth_build_role,
            build_spec=codebuild.BuildSpec.from_object(
                {
                    "version": "0.2",
                    "phases": {
                        "build": {
                            "commands": [
                                "npm install -g aws-cdk",
                                "pip install -r requirements.txt",
                                "cdk synth --no-lookups",
                            ]
                        }
                    },
                    "artifacts": {"base-directory": "cdk.out", "files": "**/*"},
                }
            ),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_5_0,
                environment_variables={
                    "MODEL_PACKAGE_GROUP_NAME": codebuild.BuildEnvironmentVariable(value=model_package_group_name),
                    "PROJECT_ID": codebuild.BuildEnvironmentVariable(value=project_id),
                    "PROJECT_NAME": codebuild.BuildEnvironmentVariable(value=project_name),
                },
            ),
        )

        # code build to include security scan over cloudformation template
        security_scan = codebuild.Project(
            self,
            "SecurityScanTooling",
            build_spec=codebuild.BuildSpec.from_object(
                {
                    "version": 0.2,
                    "env": {
                        "shell": "bash",
                        "variables": {
                            "TemplateFolder": "./*.template.json",
                            "FAIL_BUILD": "true",
                        },
                    },
                    "phases": {
                        "install": {
                            "runtime-versions": {"ruby": 3.1},
                            "commands": [
                                "export date=`date +%Y-%m-%dT%H:%M:%S.%NZ`",
                                "echo Installing cfn_nag - `pwd`",
                                "gem install cfn-nag",
                                "echo cfn_nag installation complete `date`",
                            ],
                        },
                        "build": {
                            "commands": [
                                "echo Starting cfn scanning `date` in `pwd`",
                                "echo 'RulesToSuppress:\n- id: W58\n  reason: W58 is an warning raised due to Lambda functions require permission to write CloudWatch Logs, although the lambda role contains the policy that support these permissions cgn_nag continues to through this problem (https://github.com/stelligent/cfn_nag/issues/422)' > cfn_nag_ignore.yml",  # this is temporary solution to an issue with W58 rule with cfn_nag
                                'mkdir report || echo "dir report exists"',
                                "SCAN_RESULT=$(cfn_nag_scan --deny-list-path cfn_nag_ignore.yml --input-path  ${TemplateFolder} -o json > ./report/cfn_nag.out.json && echo OK || echo FAILED)",
                                "echo Completed cfn scanning `date`",
                                "echo $SCAN_RESULT",
                                "echo $FAIL_BUILD",
                                "cat ./report/cfn_nag.out.json",
                                # """if [[ "$FAIL_BUILD" = "true" && "$SCAN_RESULT" = "FAILED" ]]; then printf "\n\nFailiing pipeline as possible insecure configurations were detected\n\n" && exit 1; fi""",
                            ]
                        },
                    },
                    "artifacts": {"files": "./report/cfn_nag.out.json"},
                }
            ),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_5_0,
            ),
        )

        source_artifact = codepipeline.Artifact(artifact_name="GitSource")
        cdk_synth_artifact = codepipeline.Artifact(artifact_name="CDKSynth")
        cfn_nag_artifact = codepipeline.Artifact(artifact_name="CfnNagScanReport")

        deploy_code_pipeline = codepipeline.Pipeline(
            self,
            "DeployPipeline",
            cross_account_keys=True,
            pipeline_name=pipeline_name,
            artifact_bucket=pipeline_artifact_bucket,
        )

        # add a source stage
        source_stage = deploy_code_pipeline.add_stage(stage_name="Source")
        source_stage.add_action(
            codepipeline_actions.CodeCommitSourceAction(
                action_name="Source",
                output=source_artifact,
                repository=deploy_app_repository,
                branch="main",
            )
        )

        # add a build stage
        build_stage = deploy_code_pipeline.add_stage(stage_name="Build")

        build_stage.add_action(
            codepipeline_actions.CodeBuildAction(
                action_name="Synth",
                input=source_artifact,
                outputs=[cdk_synth_artifact],
                project=cdk_synth_build,
            )
        )

        # add a security evaluation stage for cloudformation templates
        security_stage = deploy_code_pipeline.add_stage(stage_name="SecurityEvaluation")

        security_stage.add_action(
            codepipeline_actions.CodeBuildAction(
                action_name="CFNNag",
                input=cdk_synth_artifact,
                outputs=[cfn_nag_artifact],
                project=security_scan,
            )
        )

        # add stages to deploy to the different environments
        upload_dev_asset = self.get_upload_asset_project(env = env, account_id = Aws.ACCOUNT_ID, account_type="dev", role=cdk_synth_build_role)

        # add stages to deploy to the different environments
        deploy_code_pipeline.add_stage(
            stage_name="DeployDev",
            actions=[
                codepipeline_actions.CodeBuildAction(
                    action_name="Upolad_Assets_Dev",
                    input=source_artifact,
                    project=upload_dev_asset,
                    run_order=1
                ),
                codepipeline_actions.CloudFormationCreateUpdateStackAction(
                    action_name="Deploy_CFN_Dev",
                    run_order=2,
                    template_path=cdk_synth_artifact.at_path("dev.template.json"),
                    stack_name=f"{project_name}-{construct_id}-dev",
                    admin_permissions=False,
                    replace_on_failure=True,
                    role=iam.Role.from_role_arn(
                        self,
                        "DevActionRole",
                        f"arn:{Aws.PARTITION}:iam::{Aws.ACCOUNT_ID}:role/cdk-hnb659fds-deploy-role-{Aws.ACCOUNT_ID}-{Aws.REGION}",
                    ),
                    deployment_role=iam.Role.from_role_arn(
                        self,
                        "DevDeploymentRole",
                        f"arn:{Aws.PARTITION}:iam::{Aws.ACCOUNT_ID}:role/cdk-hnb659fds-cfn-exec-role-{Aws.ACCOUNT_ID}-{Aws.REGION}",
                    ),
                    cfn_capabilities=[
                        CfnCapabilities.AUTO_EXPAND,
                        CfnCapabilities.NAMED_IAM,
                    ],
                ),
                codepipeline_actions.ManualApprovalAction(
                    action_name="Approve_PreProd",
                    run_order=3,
                    additional_information="Approving deployment for preprod",
                ),
            ],
        )
        upload_staging_asset = self.get_upload_asset_project(env = env, account_id = preprod_account, account_type="PreProd", role=cdk_synth_build_role)

        deploy_code_pipeline.add_stage(
            stage_name="DeployPreProd",
            actions=[
                codepipeline_actions.CodeBuildAction(
                    action_name="Upolad_Assets_PreProd",
                    input=source_artifact,
                    project=upload_staging_asset,
                    run_order=1
                ),
                codepipeline_actions.CloudFormationCreateUpdateStackAction(
                    action_name="Deploy_CFN_PreProd",
                    run_order=2,
                    template_path=cdk_synth_artifact.at_path("preprod.template.json"),
                    stack_name=f"{project_name}-{construct_id}-preprod",
                    admin_permissions=False,
                    replace_on_failure=True,
                    role=iam.Role.from_role_arn(
                        self,
                        "PreProdActionRole",
                        f"arn:{Aws.PARTITION}:iam::{preprod_account}:role/cdk-hnb659fds-deploy-role-{preprod_account}-{deployment_region}",
                    ),
                    deployment_role=iam.Role.from_role_arn(
                        self,
                        "PreProdDeploymentRole",
                        f"arn:{Aws.PARTITION}:iam::{preprod_account}:role/cdk-hnb659fds-cfn-exec-role-{preprod_account}-{deployment_region}",
                    ),
                    cfn_capabilities=[
                        CfnCapabilities.AUTO_EXPAND,
                        CfnCapabilities.NAMED_IAM,
                    ],
                ),
                codepipeline_actions.ManualApprovalAction(
                    action_name="Approve_Prod",
                    run_order=3,
                    additional_information="Approving deployment for prod",
                ),
            ],
        )

        upload_prod_asset = self.get_upload_asset_project(env = env, account_id = prod_account, account_type="Prod", role=cdk_synth_build_role)
        deploy_code_pipeline.add_stage(
            stage_name="DeployProd",
            actions=[
                codepipeline_actions.CodeBuildAction(
                    action_name="Upolad_Assets_Prod",
                    input=source_artifact,
                    project=upload_prod_asset,
                    run_order=1
                ),
                codepipeline_actions.CloudFormationCreateUpdateStackAction(
                    action_name="Deploy_CFN_Prod",
                    run_order=2,
                    template_path=cdk_synth_artifact.at_path("prod.template.json"),
                    stack_name=f"{project_name}-{construct_id}-prod",
                    admin_permissions=False,
                    replace_on_failure=True,
                    role=iam.Role.from_role_arn(
                        self,
                        "ProdActionRole",
                        f"arn:{Aws.PARTITION}:iam::{prod_account}:role/cdk-hnb659fds-deploy-role-{prod_account}-{deployment_region}",
                    ),
                    deployment_role=iam.Role.from_role_arn(
                        self,
                        "ProdDeploymentRole",
                        f"arn:{Aws.PARTITION}:iam::{prod_account}:role/cdk-hnb659fds-cfn-exec-role-{prod_account}-{deployment_region}",
                    ),
                    cfn_capabilities=[
                        CfnCapabilities.AUTO_EXPAND,
                        CfnCapabilities.NAMED_IAM,
                    ],
                ),
            ],
        )

        # CloudWatch rule to trigger model pipeline when a status change event happens to the model package group
        model_event_rule = events.Rule(
            self,
            "ModelEventRule",
            event_pattern=events.EventPattern(
                source=["aws.sagemaker"],
                detail_type=["SageMaker Model Package State Change"],
                detail={
                    "ModelPackageGroupName": [model_package_group_name],
                    "ModelApprovalStatus": ["Approved", "Rejected"],
                },
            ),
            targets=[targets.CodePipeline(deploy_code_pipeline)],
        )

    def get_upload_asset_project(self, env, account_id, account_type, role):
        # assume_role = iam.Role.from_role_arn( self,
        #             f"{account_type}-upload-role",
        #             f'arn:aws:iam::{account_id}:role/cdk-hnb659fds-file-publishing-role-{account_id}-{Aws.REGION}')

        upload_asset = codebuild.PipelineProject(
            self,
            f"UploadAsset-{account_type}",
            role= role,
            build_spec=codebuild.BuildSpec.from_object(
                {
                    "version": "0.2",
                    "phases": {
                        "build": {
                            "commands": [
                                "npm install -g aws-cdk",
                                "pip install -r requirements.txt",
                                "cdk synth --no-lookups",
                                # "pwd",
                                # "ls -la -R",
                                f"python -c 'from upload_assets import upload_assets_to_s3; upload_assets_to_s3(account_id={account_id})'"
                            ]
                        }
                    },
                    "artifacts": {"base-directory": "tmp", "files": "**/*"},
                }
            ),
            environment=env
        )

        return upload_asset