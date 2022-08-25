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
    DockerImage,
    Stack,
    aws_codecommit as codecommit,
    aws_s3_assets as s3_assets,
)

from constructs import Construct

from mlops_sm_project_template.config.constants import CODE_COMMIT_REPO_NAME, PIPELINE_BRANCH


class CodeCommitStack(Stack):
    """
    CodeCommit Stack
    CodeCommit stack which provisions an AWS CodeCommit repository based on the code
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        # cloud_assembly_artifact: codepipeline.Artifact,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        repo_asset = s3_assets.Asset(
            self,
            "DeployAsset",
            path="",
            bundling=BundlingOptions(
                image=DockerImage.from_build("mlops_sm_project_template/cdk_helper_scripts/zip-image"),
                command=[
                    "sh",
                    "-c",
                    """make clean-python && zip -r /asset-output/project_template_repo.zip . -x "*.git*" -x "*cdk.out*"  -x "*.DS_Store*" """,
                ],
                output_type=BundlingOutput.ARCHIVED,
            ),
        )

        # Create source repo from seed bucket/key
        build_app_cfnrepository = codecommit.CfnRepository(
            self,
            "BuildAppCodeRepo",
            repository_name=CODE_COMMIT_REPO_NAME,
            code=codecommit.CfnRepository.CodeProperty(
                s3=codecommit.CfnRepository.S3Property(
                    bucket=repo_asset.s3_bucket_name,
                    key=repo_asset.s3_object_key,
                    object_version=None,
                ),
                branch_name=PIPELINE_BRANCH,
            ),
        )

        # Reference the newly created repository
        backend_repository = codecommit.Repository.from_repository_name(
            self, "ProjectTemplateRepo", build_app_cfnrepository.attr_name
        )
