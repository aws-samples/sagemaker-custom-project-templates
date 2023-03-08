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

import importlib
from aws_cdk import (
    Aws,
    CfnParameter,
    Stack,
    Tags,
    aws_iam as iam,
    aws_kms as kms,
    aws_sagemaker as sagemaker,
)

import constructs

from .get_approved_package import get_approved_package

from config.constants import (
    PROJECT_NAME,
    PROJECT_ID,
    MODEL_PACKAGE_GROUP_NAME,
    DEV_ACCOUNT,
    ECR_REPO_ARN,
    MODEL_BUCKET_ARN,
)

from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
from yamldataclassconfig import create_file_path_field
from config.config_mux import StageYamlDataClassConfig


@dataclass
class EndpointConfigProductionVariant(StageYamlDataClassConfig):
    """
    Endpoint Config Production Variant Dataclass
    a dataclass to handle mapping yml file configs to python class for endpoint configs
    """

    initial_instance_count: float = 1
    initial_variant_weight: float = 1
    instance_type: str = "ml.m5.2xlarge"
    variant_name: str = "AllTraffic"

    FILE_PATH: Path = create_file_path_field(
        "endpoint-config.yml", path_is_absolute=True
    )

    def get_endpoint_config_production_variant(self, model_name):
        """
        Function to handle creation of cdk glue job. It use the class fields for the job parameters.

        Parameters:
            model_name: name of the sagemaker model resource the sagemaker endpoint would use

        Returns:
            CfnEndpointConfig: CDK SageMaker CFN Endpoint Config resource
        """

        production_variant = sagemaker.CfnEndpointConfig.ProductionVariantProperty(
            initial_instance_count=self.initial_instance_count,
            initial_variant_weight=self.initial_variant_weight,
            instance_type=self.instance_type,
            variant_name=self.variant_name,
            model_name=model_name,
        )

        return production_variant


class DeployEndpointStack(Stack):
    """
    Deploy Endpoint Stack
    Deploy Endpoint stack which provisions SageMaker Model Endpoint resources.
    """

    def __init__(
        self,
        scope: constructs,
        id: str,
        **kwargs,
    ):

        super().__init__(scope, id, **kwargs)

        Tags.of(self).add("sagemaker:project-id", PROJECT_ID)
        Tags.of(self).add("sagemaker:project-name", PROJECT_NAME)
        Tags.of(self).add("sagemaker:deployment-stage", Stack.of(self).stack_name)

        # iam role that would be used by the model endpoint to run the inference
        model_execution_policy = iam.ManagedPolicy(
            self,
            "ModelExecutionPolicy",
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
                        resources=[f"arn:aws:kms:{Aws.REGION}:{DEV_ACCOUNT}:key/*"],
                    ),
                ]
            ),
        )

        if ECR_REPO_ARN:
            model_execution_policy.add_statements(
                iam.PolicyStatement(
                    actions=["ecr:Get*"],
                    effect=iam.Effect.ALLOW,
                    resources=[ECR_REPO_ARN],
                )
            )

        model_execution_role = iam.Role(
            self,
            "ModelExecutionRole",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managed_policies=[
                model_execution_policy,
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSageMakerFullAccess"
                ),
            ],
        )

        # setup timestamp to be used to trigger the custom resource update event to retrieve latest approved model and to be used with model and endpoint config resources' names
        now = datetime.now().replace(tzinfo=timezone.utc)

        timestamp = now.strftime("%Y%m%d%H%M%S")

        # get latest approved model package from the model registry (only from a specific model package group)
        latest_approved_model_package = get_approved_package()

        # Sagemaker Model
        model_name = f"{MODEL_PACKAGE_GROUP_NAME}-{timestamp}"

        model = sagemaker.CfnModel(
            self,
            "Model",
            execution_role_arn=model_execution_role.role_arn,
            model_name=model_name,
            containers=[
                sagemaker.CfnModel.ContainerDefinitionProperty(
                    model_package_name=latest_approved_model_package
                )
            ],
        )

        # Sagemaker Endpoint Config
        endpoint_config_name = f"{MODEL_PACKAGE_GROUP_NAME}-ec-{timestamp}"

        endpoint_config_production_variant = EndpointConfigProductionVariant()

        endpoint_config_production_variant.load_for_stack(self)

        # create kms key to be used by the assets bucket
        kms_key = kms.Key(
            self,
            "endpoint-kms-key",
            description="key used for encryption of data in Amazpn SageMaker Endpoint",
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

        endpoint_config = sagemaker.CfnEndpointConfig(
            self,
            "EndpointConfig",
            endpoint_config_name=endpoint_config_name,
            kms_key_id=kms_key.key_id,
            production_variants=[
                endpoint_config_production_variant.get_endpoint_config_production_variant(
                    model.model_name
                )
            ],
        )

        endpoint_config.add_depends_on(model)

        # Sagemaker Endpoint
        endpoint_name = f"{MODEL_PACKAGE_GROUP_NAME}-e"

        endpoint = sagemaker.CfnEndpoint(
            self,
            "Endpoint",
            endpoint_config_name=endpoint_config.endpoint_config_name,
            endpoint_name=endpoint_name,
        )

        endpoint.add_depends_on(endpoint_config)

        self.endpoint = endpoint
