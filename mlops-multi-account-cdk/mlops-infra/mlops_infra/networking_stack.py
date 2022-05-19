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
    Stack,
    aws_ec2 as ec2,
    aws_ssm as ssm,
    aws_iam as iam,
)
from constructs import Construct


class NetworkingStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, deploy_sm_domain, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.primary_vpc = ec2.Vpc(
            self,
            "PrimaryVPC",
            cidr="10.0.0.0/16",
            max_azs=3,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(name="Public", subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=26),
            ],
            enable_dns_hostnames=True,
            enable_dns_support=True,
            nat_gateways=1,
        )

        # VPC ID parameters
        vpc_id_param = ssm.StringParameter(
            self,
            "VPCIDParameter",
            parameter_name="/vpc/id",
            string_value=self.primary_vpc.vpc_id,
        )

        # Private Subnet IDs parameters
        private_subnet_ids_param = ssm.StringListParameter(
            self,
            "PrivateSubnetIDsParameter",
            parameter_name="/vpc/subnets/private/ids",
            string_list_value=[subnet.subnet_id for subnet in self.primary_vpc.private_subnets],
        )

        # Subnet IDs parameters
        default_sg_id_param = ssm.StringParameter(
            self,
            "DefaultSecurityGroupIDParameter",
            parameter_name="/vpc/sg/id",
            string_value=self.primary_vpc.vpc_default_security_group,
        )

        ## setup VPC endpoints - they are required for instances were the domain does not have internet access

        # S3 VPC Endpoint
        self.primary_vpc.add_gateway_endpoint("S3Endpoint", service=ec2.GatewayVpcEndpointAwsService.S3)

        # KMS VPC Endpoint
        self.primary_vpc.add_interface_endpoint("KMSEndpoint", service=ec2.InterfaceVpcEndpointAwsService.KMS)

        # ECR VPC Endpoint
        self.primary_vpc.add_interface_endpoint("ECREndpoint", service=ec2.InterfaceVpcEndpointAwsService.ECR)

        # ECR DOCKER VPC Endpoint
        self.primary_vpc.add_interface_endpoint(
            "ECRDockerEndpoint", service=ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER
        )

        if deploy_sm_domain:
            # SageMaker API VPC Endpoint
            self.primary_vpc.add_interface_endpoint(
                "SMAPIEndpoint", service=ec2.InterfaceVpcEndpointAwsService.SAGEMAKER_API
            )

            # SageMaker Runtime VPC Endpoint
            self.primary_vpc.add_interface_endpoint(
                "SMREndpoint", service=ec2.InterfaceVpcEndpointAwsService.SAGEMAKER_RUNTIME
            )

            # SageMaker Notebook VPC Endpoint
            self.primary_vpc.add_interface_endpoint(
                "SMNotebookEndpoint",
                service=ec2.InterfaceVpcEndpointAwsService.SAGEMAKER_NOTEBOOK,
            )

            # CodeCommit VPC Endpoint
            self.primary_vpc.add_interface_endpoint("CMEndpoint", service=ec2.InterfaceVpcEndpointAwsService.CODECOMMIT)

            # CodeCommit GIT VPC Endpoint
            self.primary_vpc.add_interface_endpoint(
                "CMGITEndpoint", service=ec2.InterfaceVpcEndpointAwsService.CODECOMMIT_GIT
            )

            # SSM VPC Endpoint
            self.primary_vpc.add_interface_endpoint("SSMEndpoint", service=ec2.InterfaceVpcEndpointAwsService.SSM)

            # CloudWatch VPC Endpoint
            self.primary_vpc.add_interface_endpoint("CWEndpoint", service=ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH)

            # CloudWatch Logs VPC Endpoint
            self.primary_vpc.add_interface_endpoint(
                "CWLEndpoint", service=ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS
            )

            # STS VPC Endpoint
            self.primary_vpc.add_interface_endpoint("STSEndpoint", service=ec2.InterfaceVpcEndpointAwsService.STS)

            # CodeArtifact API VPC Endpoint
            code_artifact_api_endpoint = self.primary_vpc.add_interface_endpoint(
                "CAAPIEndpoint",
                service=ec2.InterfaceVpcEndpointService(name=f"com.amazonaws.{Aws.REGION}.codeartifact.api"),
                private_dns_enabled=False,
            )

            code_artifact_api_endpoint.add_to_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "codeartifact:Describe*",
                        "codeartifact:Get*",
                        "codeartifact:List*",
                        "codeartifact:ReadFromRepository",
                    ],
                    principals=[iam.AnyPrincipal()],
                    resources=[
                        "*"
                    ],  # we can limit this to the code artifact that could be potentially as part of this repo
                )
            )

            code_artifact_api_endpoint.add_to_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "sts:GetServiceBearerToken",
                    ],
                    resources=["*"],
                    principals=[iam.AnyPrincipal()],
                    conditions={"StringEquals": {"sts:AWSServiceName": "codeartifact.amazonaws.com"}},
                )
            )

            # CodeArtifact Repositories VPC Endpoint
            code_artifact_repo_endpoint = self.primary_vpc.add_interface_endpoint(
                "CARepoEndpoint",
                service=ec2.InterfaceVpcEndpointService(name=f"com.amazonaws.{Aws.REGION}.codeartifact.repositories"),
            )

            code_artifact_repo_endpoint.add_to_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "codeartifact:Describe*",
                        "codeartifact:Get*",
                        "codeartifact:List*",
                        "codeartifact:ReadFromRepository",
                    ],
                    principals=[iam.AnyPrincipal()],
                    resources=[
                        "*"
                    ],  # we can limit this to the code artifact that could be potentially as part of this repo
                )
            )
