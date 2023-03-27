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
    RemovalPolicy,
    Fn,
    CfnTag,
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment
)

import constructs
import os

from .get_approved_package import get_approved_package

from config.constants import (
    PROJECT_NAME,
    PROJECT_ID,
    MODEL_PACKAGE_GROUP_NAME,
    DEV_ACCOUNT,
    ECR_REPO_ARN,
    MODEL_BUCKET_ARN,
    DEFAULT_DEPLOYMENT_REGION,
    CREATE_BATCH_PIPELINE,
    CREATE_ENDPOINT,
    PREPROD_ACCOUNT,
    PROD_ACCOUNT
)

from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
from yamldataclassconfig import create_file_path_field
from config.config_mux import StageYamlDataClassConfig

from deploy_endpoint.batch_inference_pipeline import get_pipeline

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

        if not CREATE_ENDPOINT and not CREATE_BATCH_PIPELINE:
            raise Exception(
                "Either create_endpoint or create_batch_pipeline must be True"
            )

        self.create_shared_resources()

        if self.is_create_endpoint():
            self.create_endpoint_resources()

        if self.is_create_batch_inference():
            self.create_batch_inference_resources()

            
    def is_create_endpoint(self):
        return CREATE_ENDPOINT == True

    def is_create_batch_inference(self):
        return CREATE_BATCH_PIPELINE == True

    def create_shared_resources(self):

        app_subnet_ids = CfnParameter(
            self,
            "subnet-ids",
            type="AWS::SSM::Parameter::Value<List<String>>",
            description="Account APP Subnets IDs",
            min_length=1,
            default="/vpc/subnets/private/ids",
        ).value_as_list

        sg_id = CfnParameter(
            self,
            "sg-id",
            type="AWS::SSM::Parameter::Value<String>",
            description="Account Default Security Group id",
            min_length=1,
            default="/vpc/sg/id",
        ).value_as_string


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

        self.model_execution_role = iam.Role(
            self,
            "ModelExecutionRole",
            role_name=f"{PROJECT_NAME}-model-execution-role",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("lambda.amazonaws.com"),
                iam.ServicePrincipal("sagemaker.amazonaws.com"),
            ),
            managed_policies=[
                model_execution_policy,
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSageMakerFullAccess"
                ),
            ],
        )

        # setup timestamp to be used to trigger the custom resource update event to retrieve latest approved model and to be used with model and endpoint config resources' names
        now = datetime.now().replace(tzinfo=timezone.utc)

        self.timestamp = now.strftime("%Y%m%d%H%M%S")

        # get latest approved model package from the model registry (only from a specific model package group)
        self.latest_approved_model_package = get_approved_package()

        # Sagemaker Model
        self.model_name = f"{MODEL_PACKAGE_GROUP_NAME}-{self.timestamp}"

        self.model = sagemaker.CfnModel(
            self,
            "Model",
            execution_role_arn=self.model_execution_role.role_arn,
            model_name=self.model_name,
            containers=[
                sagemaker.CfnModel.ContainerDefinitionProperty(
                    model_package_name=self.latest_approved_model_package
                )
            ],
            vpc_config=sagemaker.CfnModel.VpcConfigProperty(
                security_group_ids=[sg_id],
                subnets=app_subnet_ids,
            ),
        )

    def create_endpoint_resources(self):

        # Sagemaker Endpoint Config
        endpoint_config_name = f"{MODEL_PACKAGE_GROUP_NAME}-ec-{self.timestamp}"

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
                    self.model.model_name
                )
            ],
        )

        endpoint_config.add_depends_on(self.model)

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

    def create_batch_inference_resources(self):
        """
        create a sagemaker pipeline that contains batch inference
        """
        prj_name = PROJECT_NAME.lower()
        self.transform_bucket = f"{prj_name}-trnsfrm-{DEV_ACCOUNT}"
        self.pipeline_name = f"{PROJECT_NAME}-transform"

        # upload code asset to the default bucket
        BASE_DIR = os.path.dirname(os.path.realpath(__file__))

        i_bucket = s3.Bucket(
            self,
            id=self.transform_bucket,
            bucket_name=Fn.sub(
                self.transform_bucket.replace(DEV_ACCOUNT, "${AWS::AccountId}")
            ),
            versioned=False,
            removal_policy=RemovalPolicy.DESTROY,
            encryption=s3.BucketEncryption.S3_MANAGED           
        )
        i_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                sid="S3ServerAccessLogsPolicy",
                actions=["s3:PutObject"],
                resources=[
                    i_bucket.arn_for_objects(key_pattern="*"),
                    i_bucket.bucket_arn,
                ],
                principals=[
                    iam.ServicePrincipal("logging.s3.amazonaws.com")
                ],
            )
        )

        # DEV account access to objects in the bucket
        i_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                sid="AddDevPermissions",
                actions=["s3:*"],
                resources=[
                    i_bucket.arn_for_objects(key_pattern="*"),
                    i_bucket.bucket_arn,
                ],
                principals=[
                    iam.ArnPrincipal(f"arn:aws:iam::{Aws.ACCOUNT_ID}:root"),
                ],
            )
        )

        # PROD account access to objects in the bucket
        i_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                sid="AddCrossAccountPermissions",
                actions=["s3:List*", "s3:Get*", "s3:Put*"],
                resources=[
                    i_bucket.arn_for_objects(key_pattern="*"),
                    i_bucket.bucket_arn,
                ],
                principals=[
                    iam.ArnPrincipal(f"arn:aws:iam::{PREPROD_ACCOUNT}:root"),
                    iam.ArnPrincipal(f"arn:aws:iam::{PROD_ACCOUNT}:root"),
                ]
            )
        )
        source_scripts = s3_deployment.BucketDeployment(
            self,
            id=f"{prj_name}-source_scripts",
            destination_bucket=i_bucket,
            destination_key_prefix=f"{self.pipeline_name}/{self.timestamp}/source-scripts",
            sources=[s3_deployment.Source.asset(path=f"{BASE_DIR}/source_scripts")],
            role=self.model_execution_role,
        )

        pipeline_def = get_pipeline(
            region=DEFAULT_DEPLOYMENT_REGION,
            pipeline_name=self.pipeline_name,
            base_job_prefix=self.timestamp,
            role=f"arn:aws:iam::{DEV_ACCOUNT}:role/{PROJECT_NAME}-model-execution-role",
            default_bucket=self.transform_bucket,
            model_name=self.model.model_name,
        ).definition()

        pipeline_def = pipeline_def.replace(
            f"arn:aws:iam::{DEV_ACCOUNT}:role/", "arn:aws:iam::${AWS::AccountId}:role/"
        )
        pipeline_def = pipeline_def.replace(
            f"{prj_name}-trnsfrm-{DEV_ACCOUNT}",
            f"{prj_name}-trnsfrm-" + "${AWS::AccountId}",
        )
        
        assert pipeline_def.count(f"sagemaker-{DEV_ACCOUNT}") == 0, "staging and prod account may not have sagemaker bucket"

        cfn_pipeline = sagemaker.CfnPipeline(
            self,
            self.pipeline_name,
            pipeline_definition={"PipelineDefinitionBody": Fn.sub(pipeline_def)},
            pipeline_name=self.pipeline_name,
            role_arn=self.model_execution_role.role_arn,
            pipeline_description="sagemaker batch transform pipeline",
            pipeline_display_name=self.pipeline_name,
            tags=[
                CfnTag(key="sagemaker:project-id", value=PROJECT_ID),
                CfnTag(key="sagemaker:project-name", value=PROJECT_NAME),
            ],
        )