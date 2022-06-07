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
import logging
import os
from aws_cdk import (
    Aws,
    BundlingOptions,
    BundlingOutput,
    CfnParameter,
    DockerImage,
    Stack,
    Stage,
    Tags,
    aws_iam as iam,
    aws_s3_assets as s3_assets,
    aws_servicecatalog as servicecatalog,
    aws_ssm as ssm,
)
import aws_cdk

from constructs import Construct

from mlops_sm_project_template_rt.basic_project_stack import MLOpsStack
from mlops_sm_project_template_rt.constructs.ssm_construct import SSMConstruct

# Get environment variables
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Configure logging
logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)

# Create a Portfolio and Product
# see: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_servicecatalog.html
class ServiceCatalogStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        stage_name = Stage.of(self).stage_name.lower()

        execution_role_arn = CfnParameter(
            self,
            "ExecutionRoleArn",
            type="AWS::SSM::Parameter::Value<String>",
            description="The SageMaker Studio execution role",
            min_length=1,
            default="/mlops/role/lead",
        )

        portfolio_name = CfnParameter(
            self,
            "PortfolioName",
            type="String",
            description="The name of the portfolio",
            default="SageMaker Organization Templates",
            min_length=1,
        )

        portfolio_owner = CfnParameter(
            self,
            "PortfolioOwner",
            type="String",
            description="The owner of the portfolio",
            default="administrator",
            min_length=1,
            max_length=50,
        )

        product_version = CfnParameter(
            self,
            "ProductVersion",
            type="String",
            description="The product version to deploy",
            default="1.0",
            min_length=1,
        )

        # Create the launch role
        products_launch_role = iam.Role(
            self,
            "ProductLaunchRole",
            assumed_by=iam.ServicePrincipal("servicecatalog.amazonaws.com"),
            path="/service-role/",
        )

        products_launch_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonSageMakerAdmin-ServiceCatalogProductsServiceRolePolicy"
            )
        )

        products_launch_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEventBridgeFullAccess")
        )

        products_launch_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEventBridgeFullAccess")
        )

        products_launch_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AWSKeyManagementServicePowerUser")
        )

        products_launch_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("IAMFullAccess"))

        products_launch_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AWSCodeCommitFullAccess")
        )

        products_launch_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AWSCodePipelineFullAccess")
        )

        products_launch_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"))
        products_launch_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMReadOnlyAccess")
        )

        products_launch_role.add_to_policy(
            iam.PolicyStatement(
                actions=["iam:PassRole"],
                effect=iam.Effect.ALLOW,
                resources=[
                    # f"arn:aws:iam::{PREPROD_ACCOUNT}:role/*",
                    # f"arn:aws:iam::{PROD_ACCOUNT}:role/*",
                    "*"
                ],
            ),
        )

        products_launch_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "kms:Create*",
                    "kms:Describe*",
                    "kms:Enable*",
                    "kms:List*",
                    "kms:Put*",
                    "kms:Update*",
                    "kms:Revoke*",
                    "kms:Disable*",
                    "kms:Get*",
                    "kms:Delete*",
                    "kms:ScheduleKeyDeletion",
                    "kms:CancelKeyDeletion",
                ],
                effect=iam.Effect.ALLOW,
                resources=["*"],
            ),
        )

        products_launch_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "sagemaker:*",
                ],
                effect=iam.Effect.ALLOW,
                resources=[f"arn:aws:sagemaker:*:{Aws.ACCOUNT_ID}:model-package-group/*"],
            ),
        )

        portfolio = servicecatalog.Portfolio(
            self,
            "Portfolio",
            display_name=portfolio_name.value_as_string,
            provider_name=portfolio_owner.value_as_string,
            description="Organization templates for drift detection pipelines",
        )

        deploy_product = servicecatalog.CloudFormationProduct(
            self,
            "DeployProduct",
            owner=portfolio_owner.value_as_string,
            product_name="MLOps template for real-time deployment",
            product_versions=[
                servicecatalog.CloudFormationProductVersion(
                    cloud_formation_template=servicecatalog.CloudFormationTemplate.from_asset(
                        self.generate_template(MLOpsStack, f"MLOpsApp-{stage_name}", **kwargs)
                    ),
                    product_version_name=product_version.value_as_string,
                )
            ],
            description="This template includes a model building pipeline that includes a workflow to pre-process, train, evaluate and register a model.   The deploy pipeline creates a preprod and production endpoint.",
        )

        # Create portfolio associate that depends on products
        portfolio_association = servicecatalog.CfnPortfolioPrincipalAssociation(
            self,
            "PortfolioPrincipalAssociation",
            portfolio_id=portfolio.portfolio_id,
            principal_arn=execution_role_arn.value_as_string,
            principal_type="IAM",
        )

        portfolio_association.node.add_dependency(deploy_product)

        # Add product tags, and create role constraint for each product

        portfolio.add_product(deploy_product)

        Tags.of(deploy_product).add(key="sagemaker:studio-visibility", value="true")

        role_constraint = servicecatalog.CfnLaunchRoleConstraint(
            self,
            f"LaunchRoleConstraint",
            portfolio_id=portfolio.portfolio_id,
            product_id=deploy_product.product_id,
            role_arn=products_launch_role.role_arn,
            description=f"Launch as {products_launch_role.role_arn}",
        )

        role_constraint.add_depends_on(portfolio_association)

        # Create the build and deployment asset as an output to pass to pipeline stack
        build_app_asset = s3_assets.Asset(
            self,
            "BuildAsset",
            path="seed_code/build_app/",
            bundling=BundlingOptions(
                image=DockerImage.from_build("mlops_sm_project_template_rt/cdk_helper_scripts/zip-image"),
                command=[
                    "sh",
                    "-c",
                    """zip -r /asset-output/build_app.zip .""",
                ],
                output_type=BundlingOutput.ARCHIVED,
            ),
        )

        deploy_app_asset = s3_assets.Asset(
            self,
            "DeployAsset",
            path="seed_code/deploy_app/",
            bundling=BundlingOptions(
                image=DockerImage.from_build("mlops_sm_project_template_rt/cdk_helper_scripts/zip-image"),
                command=[
                    "sh",
                    "-c",
                    """zip -r /asset-output/deploy_app.zip .""",
                ],
                output_type=BundlingOutput.ARCHIVED,
            ),
        )

        build_app_asset.grant_read(grantee=products_launch_role)
        deploy_app_asset.grant_read(grantee=products_launch_role)

        # Output the deployment bucket and key, for input into pipeline stack
        self.export_ssm(
            "CodeSeedBucket",
            "/mlops/code/seed_bucket",
            build_app_asset.s3_bucket_name,
        )
        self.export_ssm(
            "CodeBuildKey",
            "/mlops/code/build",
            build_app_asset.s3_object_key,
        )
        self.export_ssm(
            "CodeDeployKey",
            "/mlops/code/deploy",
            deploy_app_asset.s3_object_key,
        )

        # issue with pipeline encryption key created with an alias similar https://github.com/aws/aws-cdk/issues/4374
        # create kms key to be used by the assets bucket
        # kms_key = kms.Key(
        #     self,
        #     "ArtifactsBucketKMSKey",
        #     description="key used for encryption of data in Amazon S3",
        #     enable_key_rotation=True
        # )

        # pipeline_artifact_bucket = s3.Bucket(
        #     self,
        #     "S3Artifact",
        #     bucket_name=f"mlops-pipeline-{construct_id}-{Aws.REGION}",
        #     encryption_key=kms_key,
        #     versioned=True,
        #     removal_policy=aws_cdk.RemovalPolicy.DESTROY,
        # )

        # self.export_ssm(
        #     "PipelineArtifactBucket",
        #     "/mlops/pipeline/bucket",
        #     pipeline_artifact_bucket.bucket_name,
        # )

        SSMConstruct(self, "MLOpsSSM")

    def export_ssm(self, key: str, param_name: str, value: str):
        param = ssm.StringParameter(self, key, parameter_name=param_name, string_value=value)

    def generate_template(self, stack: Stack, stack_name: str, **kwargs):
        """Create a CFN template from a stack

        Args:
            stack (cdk.Stack): cdk Stack to synthesize into a CFN template
            stack_name (str): Name to assign to the stack

        Returns:
            [str]: path of the CFN template
        """
        stage = aws_cdk.App()
        stack = stack(stage, stack_name, synthesizer=aws_cdk.BootstraplessSynthesizer(), **kwargs)
        assembly = stage.synth()
        template_full_path = assembly.stacks[0].template_full_path

        self.remove_policy(template_full_path, template_full_path)

        return template_full_path

    def remove_policy(self, input_path: str, output_path: str):
        """
        Remove policy that CDK adds when part of the role_arn is provided from a cloudformation parameter
        """
        with open(input_path, "r") as f:
            t = json.load(f)

        # Remove policies
        policy_list = [
            k for k in t["Resources"] if t["Resources"][k]["Type"] == "AWS::IAM::Policy" and ("deployPreProdActionRolePolicy" in k or "deployProdActionRolePolicy" in k)
        ]
        
        for p in policy_list:
            logger.debug(f"Removing Policy {p}")
            del t["Resources"][p]

        # Remove policy dependencies
        depends_on = [k for k in t["Resources"] if "DependsOn" in t["Resources"][k]]
        for d in depends_on:
            for p in policy_list:
                if p in t["Resources"][d]["DependsOn"]:
                    logger.debug(f"Removing DependsOn {p}")
                    t["Resources"][d]["DependsOn"].remove(p)
            if len(t["Resources"][d]["DependsOn"]) == 0:
                del t["Resources"][d]["DependsOn"]

        # Save file back
        logger.info(f"Writing template to: {output_path}")
        with open(output_path, "w") as f:
            json.dump(t, f, indent=2)
