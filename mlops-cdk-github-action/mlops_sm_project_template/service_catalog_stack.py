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
    aws_lambda as lambda_,
)
import aws_cdk

from constructs import Construct
from aws_cdk.aws_ecr_assets import DockerImageAsset

from mlops_sm_project_template.config.constants import (
    DEV_ACCOUNT,
    DEFAULT_DEPLOYMENT_REGION
)

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
            default="/sagemaker/execution/role",
        ).value_as_string

        portfolio_name = CfnParameter(
            self,
            "PortfolioName",
            type="String",
            description="The name of the portfolio",
            default="SageMaker Organization Templates",
            min_length=1,
        ).value_as_string

        portfolio_owner = CfnParameter(
            self,
            "PortfolioOwner",
            type="String",
            description="The owner of the portfolio",
            default="administrator",
            min_length=1,
            max_length=50,
        ).value_as_string

        product_version = CfnParameter(
            self,
            "ProductVersion",
            type="String",
            description="The product version to deploy",
            default="1.0",
            min_length=1,
        ).value_as_string

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
            iam.ManagedPolicy.from_aws_managed_policy_name("AWSKeyManagementServicePowerUser")
        )

        products_launch_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("IAMFullAccess"))

        products_launch_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"))
        products_launch_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMReadOnlyAccess")
        )
        products_launch_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryFullAccess")
        )

        products_launch_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("SecretsManagerReadWrite")
        )

        products_launch_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AWSLambda_FullAccess")
        )

        products_launch_role.add_to_policy(
            iam.PolicyStatement(
                actions=["iam:PassRole"],
                effect=iam.Effect.ALLOW,
                resources=[
                    "*"
                    # TODO lock this policy to only certain roles from the other account that are used for deploying the solution as defined in templates/pipeline_constructs/deploy_pipeline_stack.py
                ],
            ),
        )

        products_launch_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "sqs:*"
                ],
                effect=iam.Effect.ALLOW,
                resources=["*"],
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
            display_name=portfolio_name,
            provider_name=portfolio_owner,
            description="Organization templates for drift detection pipelines",
        )

        # Create portfolio associate that depends on products
        portfolio_association = servicecatalog.CfnPortfolioPrincipalAssociation(
            self,
            "PortfolioPrincipalAssociation",
            portfolio_id=portfolio.portfolio_id,
            principal_arn=execution_role_arn,
            principal_type="IAM",
        )

        # product = servicecatalog.CloudFormationProduct(
        #     self,
        #     "DeployProduct",
        #     owner=portfolio_owner,
        #     product_name=MLOpsStack.TEMPLATE_NAME,
        #     product_versions=[
        #         servicecatalog.CloudFormationProductVersion(
        #             cloud_formation_template=servicecatalog.CloudFormationTemplate.from_asset(
        #                 self.generate_template(MLOpsStack, f"MLOpsApp-{stage_name}", **kwargs)
        #             ),
        #             product_version_name=product_version,
        #         )
        #     ],
        #     description=MLOpsStack.DESCRIPTION,
        # )

        # portfolio_association.node.add_dependency(product)

        # # Add product tags, and create role constraint for each product

        # portfolio.add_product(product)

        # Tags.of(product).add(key="sagemaker:studio-visibility", value="true")

        # role_constraint = servicecatalog.CfnLaunchRoleConstraint(
        #     self,
        #     f"LaunchRoleConstraint",
        #     portfolio_id=portfolio.portfolio_id,
        #     product_id=product.product_id,
        #     role_arn=products_launch_role.role_arn,
        #     description=f"Launch as {products_launch_role.role_arn}",
        # )
        # role_constraint.add_depends_on(portfolio_association)

        # uncomment this block if you want to create service catalog products based on all templates
        # make sure you comment out lines 202-234
        self.deploy_all_products(
            portfolio_association,
            portfolio,
            products_launch_role,
            portfolio_owner,
            product_version,
            stage_name,
            **kwargs,
        )

        # Create the build and deployment asset as an output to pass to pipeline stack
        zip_image = DockerImage.from_build("mlops_sm_project_template/cdk_helper_scripts/zip-image")

        build_app_asset = s3_assets.Asset(
            self,
            "BuildAsset",
            path="seed_code/build_app/",
            bundling=BundlingOptions(
                image=zip_image,
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
                image=zip_image,
                command=[
                    "sh",
                    "-c",
                    """zip -r /asset-output/deploy_app.zip .""",
                ],
                output_type=BundlingOutput.ARCHIVED,
            ),
        )

        trigger_github_action_lambda_asset = s3_assets.Asset(
            self,
            "BuildSeedGithubLambdaAsset",
            path="functions/trigger_github_repo/",
            bundling=BundlingOptions(
                image=lambda_.Runtime.PYTHON_3_9.bundling_image,
                command=[
                    "sh",
                    "-c",
                    """pip install -r requirements.txt -t /asset-output/package && cp -au . /asset-output/package && cd /asset-output/package && zip -r /asset-output/trigger_github_repo.zip * && cd /asset-output && rm -rf package"""
                ],
                output_type=BundlingOutput.ARCHIVED,
            ),
        )

        # Build the docker image for lambda function, which will responsible for seeding the code and
        # create GitHub secrets
        github_secret_create_lambada_ecr_asset = DockerImageAsset(self, "DockerLambdaForGithubSecretUpdate",
                                                                  directory="functions/github_repo_secrets/")

        github_secret_create_lambada_ecr_asset.repository.grant_pull_push(grantee=products_launch_role)
        build_app_asset.grant_read(grantee=products_launch_role)
        deploy_app_asset.grant_read(grantee=products_launch_role)
        trigger_github_action_lambda_asset.grant_read(grantee=products_launch_role)

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

        self.export_ssm(
            "LambdaFunctionAssetBucket",
            "/mlops/lambda_function/bucket",
            trigger_github_action_lambda_asset.s3_bucket_name,
        )
        self.export_ssm(
            "GithubActionTriggerLambdaFunctionAsset",
            "/mlops/lambda/github-action-trigger",
            trigger_github_action_lambda_asset.s3_object_key,
        )

        self.export_ssm(
            "DockerLambdaForGithubSecretAsset",
            "/mlops/ecr/repo/github-secret-create-lambada",
            github_secret_create_lambada_ecr_asset.repository.repository_name
        )

        self.export_ssm(
            "DockerLambdaForGithubSecretAssetTag",
            "/mlops/ecr/repo/github-secret-create-lambada-ecr-tag",
            github_secret_create_lambada_ecr_asset.image_tag
        )

        dev_account_id_param = ssm.StringParameter(
            self,
            "DevAccountIDParameter",
            parameter_name="/mlops/dev/account_id",
            string_value=DEV_ACCOUNT,
        )

    def deploy_all_products(
            self,
            portfolio_association: servicecatalog.CfnPortfolioPrincipalAssociation,
            portfolio: servicecatalog.Portfolio,
            products_launch_role: iam.Role,
            portfolio_owner: str,
            product_version: str,
            stage_name: str,
            templates_directory: str = "mlops_sm_project_template/templates",
            **kwargs,
    ):

        i = 0  # used as a counter for the products

        for file in os.listdir(templates_directory):
            filename = os.fsdecode(file)
            if filename.endswith("_stack.py"):
                template_py_file = filename[:-3]

                template_module = importlib.import_module(f"mlops_sm_project_template.templates.{template_py_file}")

                template_py_file = template_py_file.replace("_", "-")

                product = servicecatalog.CloudFormationProduct(
                    self,
                    f"Product-{template_py_file}",
                    owner=portfolio_owner,
                    product_name=template_module.MLOpsStack.TEMPLATE_NAME,
                    product_versions=[
                        servicecatalog.CloudFormationProductVersion(
                            cloud_formation_template=servicecatalog.CloudFormationTemplate.from_asset(
                                self.generate_template(
                                    template_module.MLOpsStack,
                                    f"{template_py_file}-{stage_name}",
                                    **kwargs,
                                )
                            ),
                            product_version_name=product_version,
                        )
                    ],
                    description=template_module.MLOpsStack.DESCRIPTION,
                )

                portfolio_association.node.add_dependency(product)

                # Add product tags, and create role constraint for each product

                portfolio.add_product(product)

                Tags.of(product).add(key="sagemaker:studio-visibility", value="true")

                role_constraint = servicecatalog.CfnLaunchRoleConstraint(
                    self,
                    f"LaunchRoleConstraint{i}",
                    portfolio_id=portfolio.portfolio_id,
                    product_id=product.product_id,
                    role_arn=products_launch_role.role_arn,
                    description=f"Launch as {products_launch_role.role_arn}",
                )
                role_constraint.add_depends_on(portfolio_association)

                i += 1

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
            k
            for k in t["Resources"]
            if t["Resources"][k]["Type"] == "AWS::IAM::Policy"
            and ("deployPreProdActionRolePolicy" in k or "deployProdActionRolePolicy" in k)
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
