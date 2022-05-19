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
    aws_iam as iam,
    aws_ssm as ssm,
)

from constructs import Construct


class SMRoles(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        s3_bucket_prefix: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # create policies required for the roles

        sm_deny_policy = iam.Policy(
            self,
            "sm-deny-policy",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.DENY,
                    actions=[
                        "sagemaker:CreateProject",
                    ],
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.DENY,
                    actions=["sagemaker:UpdateModelPackage"],
                    resources=["*"],
                ),
            ],
        )

        services_policy = iam.Policy(
            self,
            "services-policy",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "lambda:Create*",
                        "lambda:Update*",
                        "lambda:Invoke*",
                    ],
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "sagemaker:ListTags",
                    ],
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "codecommit:GitPull",
                        "codecommit:GitPush",
                        "codecommit:*Branch*",
                        "codecommit:*PullRequest*",
                        "codecommit:*Commit*",
                        "codecommit:GetDifferences",
                        "codecommit:GetReferences",
                        "codecommit:GetRepository",
                        "codecommit:GetMerge*",
                        "codecommit:Merge*",
                        "codecommit:DescribeMergeConflicts",
                        "codecommit:*Comment*",
                        "codecommit:*File",
                        "codecommit:GetFolder",
                        "codecommit:GetBlob",
                    ],
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "ecr:BatchGetImage",
                        "ecr:BatchCheckLayerAvailability",
                        "ecr:GetDownloadUrlForLayer",
                        "ecr:GetRepositoryPolicy",
                        "ecr:DescribeRepositories",
                        "ecr:DescribeImages",
                        "ecr:ListImages",
                        "ecr:GetAuthorizationToken",
                        "ecr:GetLifecyclePolicy",
                        "ecr:GetLifecyclePolicyPreview",
                        "ecr:ListTagsForResource",
                        "ecr:DescribeImageScanFindings",
                        "ecr:CreateRepository",
                        "ecr:CompleteLayerUpload",
                        "ecr:UploadLayerPart",
                        "ecr:InitiateLayerUpload",
                        "ecr:PutImage",
                    ],
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "servicecatalog:*",
                    ],
                    resources=["*"],
                ),
            ],
        )

        kms_policy = iam.Policy(
            self,
            "kms-policy",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "kms:CreateGrant",
                        "kms:Decrypt",
                        "kms:DescribeKey",
                        "kms:Encrypt",
                        "kms:ReEncrypt",
                        "kms:GenerateDataKey",
                    ],
                    resources=["*"],
                )
            ],
        )

        s3_policy = iam.Policy(
            self,
            "s3-policy",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "s3:AbortMultipartUpload",
                        "s3:DeleteObject",
                        "s3:Describe*",
                        "s3:GetObject",
                        "s3:PutBucket*",
                        "s3:PutObject",
                        "s3:PutObjectAcl",
                        "s3:GetBucketAcl",
                        "s3:GetBucketLocation",
                    ],
                    resources=[
                        "arn:aws:s3:::{}*/*".format(s3_bucket_prefix),
                        "arn:aws:s3:::{}*".format(s3_bucket_prefix),
                    ],
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["s3:ListBucket"],
                    resources=["arn:aws:s3:::{}*".format(s3_bucket_prefix)],
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.DENY,
                    actions=["s3:DeleteBucket*"],
                    resources=["*"],
                ),
            ],
        )

        ## create role for each persona

        # role for Data Scientist persona
        self.data_scientist_role = iam.Role(
            self,
            "data-scientist-role",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("lambda.amazonaws.com"),
                iam.ServicePrincipal("sagemaker.amazonaws.com"),
            ),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMReadOnlyAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSLambda_ReadOnlyAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSCodeCommitReadOnly"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryReadOnly"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess"),
            ],
        )

        sm_deny_policy.attach_to_role(self.data_scientist_role)
        services_policy.attach_to_role(self.data_scientist_role)
        kms_policy.attach_to_role(self.data_scientist_role)
        s3_policy.attach_to_role(self.data_scientist_role)

        ssm.StringParameter(
            self,
            "ssm-sg-ds-role",
            parameter_name="/mlops/role/ds",
            string_value=self.data_scientist_role.role_arn,
        )

        # role for Lead Data Scientist persona
        self.lead_data_scientist_role = iam.Role(
            self,
            "lead-data-scientist-role",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("lambda.amazonaws.com"),
                iam.ServicePrincipal("sagemaker.amazonaws.com"),
            ),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMReadOnlyAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSLambda_ReadOnlyAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSCodeCommitReadOnly"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryReadOnly"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess"),
            ],
        )

        services_policy.attach_to_role(self.lead_data_scientist_role)
        kms_policy.attach_to_role(self.lead_data_scientist_role)
        s3_policy.attach_to_role(self.lead_data_scientist_role)

        ssm.StringParameter(
            self,
            "ssm-sg-lead-role",
            parameter_name="/mlops/role/lead",
            string_value=self.lead_data_scientist_role.role_arn,
        )

        # default role for sagemaker persona
        self.sagemaker_studio_role = iam.Role(
            self,
            "sagemaker-studio-role",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("lambda.amazonaws.com"),
                iam.ServicePrincipal("sagemaker.amazonaws.com"),
            ),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMReadOnlyAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSLambda_ReadOnlyAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSCodeCommitReadOnly"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryReadOnly"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess"),
            ],
        )

        services_policy.attach_to_role(self.sagemaker_studio_role)
        kms_policy.attach_to_role(self.sagemaker_studio_role)
        s3_policy.attach_to_role(self.sagemaker_studio_role)

        ssm.StringParameter(
            self,
            "ssm-sg-execution-role",
            parameter_name="/mlops/role/execution",
            string_value=self.sagemaker_studio_role.role_arn,
        )
