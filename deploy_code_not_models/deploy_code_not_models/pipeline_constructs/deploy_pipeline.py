from aws_cdk import (
    Aws,
    CfnCapabilities,
    aws_s3 as s3,
    aws_iam as iam,
    aws_events as events,
    aws_events_targets as targets,
    aws_codecommit as codecommit,
    aws_codebuild as codebuild,
    aws_codepipeline_actions as codepipeline_actions,
    aws_codepipeline as codepipeline,
)

from constructs import Construct


class DeployPipeline(Construct):
    def __init__(
        self,
        scope: Construct,
        project_id: str,
        project_name: str,
        construct_id: str,
        env_name: str,
        account_id: str,
        model_package_group_name: str,
        s3_artifact: s3.IBucket,
        cdk_synth_build_role: iam.IRole,
        deploy_app_repository: codecommit.IRepository,
    ) -> None:
        super().__init__(scope, construct_id)

        pipeline_name = f"{project_name}-{construct_id}-{env_name}"

        cdk_synth_build = codebuild.PipelineProject(
            self,
            f"{env_name}CDKSynthBuild",
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
                    "MODEL_PACKAGE_GROUP_NAME": codebuild.BuildEnvironmentVariable(
                        value=model_package_group_name
                    ),
                    "PROJECT_ID": codebuild.BuildEnvironmentVariable(value=project_id),
                    "PROJECT_NAME": codebuild.BuildEnvironmentVariable(
                        value=project_name
                    ),
                    "ACCOUNT_ID": codebuild.BuildEnvironmentVariable(value=account_id),
                },
            ),
        )

        # code build to include security scan over cloudformation template
        security_scan = codebuild.Project(
            self,
            f"SecurityScan{env_name}",
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
                            "runtime-versions": {"ruby": 2.6},
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
                                "SCAN_RESULT=$(cfn_nag_scan --fail-on-warnings --deny-list-path cfn_nag_ignore.yml --input-path  ${TemplateFolder} -o json > ./report/cfn_nag.out.json && echo OK || echo FAILED)",
                                "echo Completed cfn scanning `date`",
                                "echo $SCAN_RESULT",
                                "echo $FAIL_BUILD",
                                """if [[ "$FAIL_BUILD" = "true" && "$SCAN_RESULT" = "FAILED" ]]; then printf "\n\nFailiing pipeline as possible insecure configurations were detected\n\n" && exit 1; fi""",
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
            f"{env_name}DeployPipeline",
            cross_account_keys=True,
            pipeline_name=pipeline_name,
            artifact_bucket=s3_artifact,
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

        deploy_code_pipeline.add_stage(
            stage_name=f"Deploy{env_name}",
            actions=[
                codepipeline_actions.CloudFormationCreateUpdateStackAction(
                    action_name=f"Deploy_CFN_{env_name}",
                    run_order=1,
                    template_path=cdk_synth_artifact.at_path(
                        f"{env_name}.template.json"
                    ),
                    stack_name=f"{project_name}-{construct_id}-{env_name}",
                    admin_permissions=False,
                    replace_on_failure=True,
                    role=iam.Role.from_role_arn(
                        self,
                        f"{env_name}ActionRole",
                        f"arn:{Aws.PARTITION}:iam::{account_id}:role/cdk-hnb659fds-deploy-role-{account_id}-{Aws.REGION}",
                    ),
                    deployment_role=iam.Role.from_role_arn(
                        self,
                        f"{env_name}DeploymentRole",
                        f"arn:{Aws.PARTITION}:iam::{account_id}:role/cdk-hnb659fds-cfn-exec-role-{account_id}-{Aws.REGION}",
                    ),
                    cfn_capabilities=[
                        CfnCapabilities.AUTO_EXPAND,
                        CfnCapabilities.NAMED_IAM,
                    ],
                )
            ],
        )

        dev_model_event_rule = events.Rule(
            self,
            f"{env_name}ModelEventRule",
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

