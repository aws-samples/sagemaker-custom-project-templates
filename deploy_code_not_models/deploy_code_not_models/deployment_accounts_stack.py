"""
This stack creates the roles and policies needed in the deployment accounts (dev, stg, prod)
"""


from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_ssm as ssm,
    Aws
)

from constructs import Construct


class DeploymentAccountResources(Stack):

    def __init__(self, scope: Construct, construct_id: str, tooling_account: str, project_name: str, project_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        '''
        create a role to be assumed by build step from the tooling account, to deploy the SM pipeline
        needs to be able to read from SSM too

        create a role for the sagemaker pipeline that is allowed to write to the corresponding model registry in tooling
        write that role to ssm to be retrieved during the buildspec step

        '''
        ssm_parameter_name = f"/mlops/tooling_impl/sagemaker_role_arn"

        # create a role for the codebuild step
        codebuild_step_role = iam.Role(
            self, 'CodeBuildRole',
            role_name=f'CrossAccountCodeBuildStep-{project_name}-{project_id}',
            assumed_by=iam.ArnPrincipal(f"arn:aws:iam::{tooling_account}:root")
        )
        
        codebuild_step_role.add_to_policy(
            iam.PolicyStatement(
                actions=['sagemaker:*'],
                resources=['*'],
                effect=iam.Effect.ALLOW
            )
        )

        codebuild_step_role.add_to_policy(
            iam.PolicyStatement(
                actions=['ssm:GetParameter'],
                resources=['*'],
                effect=iam.Effect.ALLOW
                        
            )
        )

        codebuild_step_role.add_to_policy(
            iam.PolicyStatement(
                actions=['iam:PassRole'],
                resources=['*'],
                effect=iam.Effect.ALLOW
                        
            )
        )

        codebuild_step_role.add_to_policy(
            iam.PolicyStatement(
                actions=['s3:*'],
                resources=[
                    f'arn:aws:s3:::mlops-{project_name}-{project_id}',
                    f'arn:aws:s3:::mlops-{project_name}-{project_id}/*'
                ]
            )
        )

        codebuild_step_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "kms:Decrypt",
                    "kms:DescribeKey",
                    "kms:Encrypt",
                    "kms:ReEncrypt*",
                    "kms:GenerateDataKey*"
                ],
                resources=[
                    '*'
                ],
                effect=iam.Effect.ALLOW
            )
        )

        sagemaker_role = iam.Role(
            self, 'SagemakerRole',
            assumed_by=iam.ServicePrincipal('sagemaker.amazonaws.com')
        )

        sagemaker_role.add_to_policy(
            iam.PolicyStatement(
                actions=['sagemaker:*'],
                resources=['*'],
                effect=iam.Effect.ALLOW
            )
        )

        sagemaker_role.add_to_policy(
            iam.PolicyStatement(
                actions=['sagemaker:CreateModelPackage'],
                resources=[f'arn:aws:sagemaker:{Aws.REGION}:{tooling_account}:model-package/*'],
                effect=iam.Effect.ALLOW
            )
        )

        sagemaker_role.add_to_policy(
            iam.PolicyStatement(
                actions=['s3:*'],
                resources=['*'],
                effect=iam.Effect.ALLOW
            )
        )  

        sagemaker_role.add_to_policy(
            iam.PolicyStatement(
                actions=['iam:PassRole'],
                resources=['*'],
                effect=iam.Effect.ALLOW
                        
            )
        )

        sagemaker_role.add_to_policy(
            iam.PolicyStatement(
                actions=['kms:*'],
                resources=[f'arn:aws:kms:{Aws.REGION}:{tooling_account}:key/*'],
                effect=iam.Effect.ALLOW
                        
            )
        )  

        sagemaker_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess")
        )

        sagemaker_role.add_to_policy(
            iam.PolicyStatement(
                actions=['s3:*'],
                resources=[
                    f'arn:aws:s3:::mlops-{project_name}-{project_id}',
                    f'arn:aws:s3:::mlops-{project_name}-{project_id}/*'
                ]
            )
        )

        ssm.StringParameter(
            self, 'sagemaker_role_arn',
            parameter_name=ssm_parameter_name,
            string_value=sagemaker_role.role_arn
        )



