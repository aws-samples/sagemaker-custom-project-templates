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

import json
import subprocess

from aws_cdk import (
    Aws,
    CfnParameter,
    CfnTag,
    aws_iam as iam,
    aws_kms as kms,
    aws_sagemaker as sagemaker,
)

from constructs import Construct

from config.constants import (
    PROJECT_NAME,
    PROJECT_ID,
    MODEL_BUCKET_ARN,
    SM_PIPELINE_DEFINITION_S3LOCATION,
    # DATA_BUCKET,
    # DATA_KMS_KEY
)

from datetime import datetime, timezone

subprocess.check_call(f"aws s3 cp {SM_PIPELINE_DEFINITION_S3LOCATION} inferencepipeline.json".split())

with open("inferencepipeline.json") as f:
    SM_PIPELINE_DEFINITION = json.dumps(json.load(f))


class DeploySMPipelineConstruct(Construct):
    """
    Deploy SageMaker Pipeline construct. This construct creates:
    - a SageMaker Pipeline whose definition location is taken from SSM
    - an IAM Role and Policy to execute the SageMaker Pipeline

    (TODO) a dedicated "outputs" s3 bucket for the outputs of the SageMaker Pipeline in each accountw

    (TODO) an Event Rule to trigger Pipeline run when Abstraction Layer job is finished (take Abs. Layer SNS notification as trigger)
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        **kwargs,
    ):

        super().__init__(scope, id, **kwargs)

        # iam role that would be used by the model endpoint to run the inference
        smpipeline_execution_policy = iam.ManagedPolicy(
            self,
            "SMPipelineExecutionPolicy",
            document=iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        actions=[
                            "s3:Put*",
                            "s3:Get*",
                            "s3:List*",
                        ],
                        effect=iam.Effect.ALLOW,
                        resources=[
                            MODEL_BUCKET_ARN,
                            f"{MODEL_BUCKET_ARN}/*",
                            # DATA_BUCKET_ARN,
                            # f"{DATA_BUCKET_ARN}/*",
                        ],
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
                        resources=[
                            f"arn:aws:kms:{Aws.REGION}:{Aws.ACCOUNT_ID}:key/*",
                            # DATA_KMS_KEY_ARN
                        ],
                    ),
                ]
            ),
        )

        # We need to define a role name and pass it to the string replacement
        smpipeline_execution_role = iam.Role(
            self,
            "SMPipelineExecutionRole",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managed_policies=[
                smpipeline_execution_policy,
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSageMakerFullAccess"
                ),
                # TODO: Remove once outputs S3 bucket created
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonS3FullAccess"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonOpenSearchServiceFullAccess"
                ), 
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonElasticContainerRegistryPublicFullAccess"
                ), 
            ],
        )

        # This is a workaround to string replace the placeholder role in the SM_PIPELINE_DEFINITION with the one created here
        smpipeline_definition_string = SM_PIPELINE_DEFINITION.replace(
            "REPLACEROLE/REPLACEROLE", smpipeline_execution_role.role_arn
        )

        # https://docs.amazonaws.cn/en_us/AWSCloudFormation/latest/UserGuide/aws-resource-sagemaker-pipeline.html
        smpipeline_config = {"PipelineDefinitionBody": smpipeline_definition_string}

        # setup timestamp to be used to trigger the custom resource update event to retrieve latest approved model and to be used with model and endpoint config resources' names
        now = datetime.now().replace(tzinfo=timezone.utc)

        timestamp = now.strftime("%Y%m%d%H%M%S")

        # Sagemaker Pipeline
        smpipeline_name = f"{PROJECT_NAME}-infpipeline"

        smpipeline = sagemaker.CfnPipeline(
            self,
            "SMPipeline",
            role_arn=smpipeline_execution_role.role_arn,
            pipeline_definition=smpipeline_config,
            pipeline_name=smpipeline_name,
            pipeline_description="SageMaker Pipeline to run batch transform jobs from SM Model",
            tags=[CfnTag(key="creation_timestamp", value=timestamp)],
        )

        self.smpipeline = smpipeline

        # TODO: Add EventBridge to read trigger when new data OR new SageMaker pipeline definition
