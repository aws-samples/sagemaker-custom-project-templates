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
    Environment,
    Stack,
    Stage,
    aws_codebuild as codebuild,
    aws_codecommit as codecommit,
    pipelines,
)

from constructs import Construct

from mlops_sm_project_template.config.constants import (
    APP_PREFIX,
    CODE_COMMIT_REPO_NAME,
    DEFAULT_DEPLOYMENT_REGION,
    PIPELINE_BRANCH,
)

from mlops_sm_project_template.service_catalog_stack import ServiceCatalogStack


class CoreStage(Stage):
    """
    Core Stage
    Core Stage which handles the creation of stacks that would be used to deploy key components service catalog product for mlops project template for sagemaker projects
    - ServiceCatalogStack: handles the creation of service catalog related resources and deploy product for sagemaker projects
    """

    def __init__(self, scope: Construct, id: str, config_set: dict, **kwargs) -> None:

        super().__init__(scope, id, **kwargs)

        service_catalog_stack = ServiceCatalogStack(self, "MLOpsServiceCatalog", config_set=config_set, **kwargs)


class PipelineStack(Stack):
    """
    Pipeline Stack
    Pipeline stack which provisions code pipeline for CICD deployments for the project resources.
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        config_set: dict,
        # cloud_assembly_artifact: codepipeline.Artifact,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        backend_repository = codecommit.Repository.from_repository_name(
            self, "ProjectTemplateRepo", repository_name=CODE_COMMIT_REPO_NAME
        )

        # create a CodePipeline resource which creates the following:
        # - source stage linked to the code commit repo listensing to the master branch update events
        # - build stage which runs cdk synth which generated the cloudformation resources in the pipeline artefact cloud assembly
        # - self mutation stage which handles pipeline changes based on latest pushed code to the repository
        # - assets stage which pushes zipped assets such as lambda function code, lambda layers and any other assets to a managed s3 bucket (the bucket that was created as part of cdk toolkit stack)
        pipeline = pipelines.CodePipeline(
            self,
            "Pipeline",
            self_mutation=True,
            cross_account_keys=True,
            pipeline_name=f"{APP_PREFIX}-service-catalog-{PIPELINE_BRANCH}-{config_set['SET_NAME']}",
            docker_enabled_for_synth=True,
            docker_enabled_for_self_mutation=True,
            synth=pipelines.ShellStep(  # build stage in code pipeline
                "Synth",
                input=pipelines.CodePipelineSource.code_commit(repository=backend_repository, branch=PIPELINE_BRANCH),
                commands=[
                    "npm install -g aws-cdk",
                    "pip install -r requirements.txt",
                    "cdk synth --no-lookups",
                ],
            ),
        )

        pipeline.add_wave(
            "SecurityEvaluation",
            post=[
                pipelines.CodeBuildStep(
                    "cfn-nag",
                    commands=[],
                    input=pipeline.synth,
                    primary_output_directory="./report",
                    partial_build_spec=codebuild.BuildSpec.from_object(
                        {
                            "version": 0.2,
                            "env": {
                                "shell": "bash",
                                "variables": {
                                    "TemplateFolder": "./**/*.template.json",
                                    "FAIL_BUILD": "false",
                                },
                            },
                            "phases": {
                                "install": {
                                    "runtime-versions": {"ruby": 2.7},
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
                        }
                    ),
                )
            ],
        )

        # add dev stage for resources that we want to deploy in this account and potentially in other accounts as well
        dev_stage = pipeline.add_stage(
            CoreStage(
                self,
                "DEV",
                config_set=config_set,
                env=Environment(account=config_set["DEV_ACCOUNT"], region=DEFAULT_DEPLOYMENT_REGION),
            )
        )
