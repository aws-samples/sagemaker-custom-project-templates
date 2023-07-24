import os

from aws_cdk import (
    Aws,
    Stack,
    Tags,
    aws_s3 as s3,
    aws_iam as iam,
    aws_kms as kms,
    aws_sagemaker as sagemaker,
    aws_s3_assets as s3_assets,
    aws_codecommit as codecommit,
    BundlingOptions,
    BundlingOutput,
    DockerImage
)

import aws_cdk
from constructs import Construct
from pathlib import Path

from deploy_code_not_models.pipeline_constructs.build_pipeline import BuildPipeline
from deploy_code_not_models.pipeline_constructs.deploy_pipeline import DeployPipeline


class ToolingAccountResources(Stack):

    def __init__(self, scope: Construct, construct_id: str, dev_account: str, stg_account: str, prod_account: str, project_name: str, project_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        Tags.of(self).add("sagemaker:project-id", project_id)
        Tags.of(self).add("sagemaker:project-name", project_name)

        kms_key = kms.Key(
            self,
            f"ArtifactsBucketKMSKey",
            description="key used for encryption of data in Amazon S3",
            enable_key_rotation=True,
            policy=iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        actions=["kms:*"],
                        effect=iam.Effect.ALLOW,
                        resources=["*"],
                        principals=[
                            iam.ArnPrincipal(f"arn:aws:iam::{Aws.ACCOUNT_ID}:root"),
                            iam.ArnPrincipal(f"arn:aws:iam::{stg_account}:root"),
                            iam.ArnPrincipal(f"arn:aws:iam::{prod_account}:root")
                            ],
                    )
                ]
            ),
        )

        s3_artifact = s3.Bucket(
            self,
            "S3Artifact",
            bucket_name=f"mlops-{project_name}-{project_id}",
            encryption_key=kms_key,
            versioned=True,
            removal_policy=aws_cdk.RemovalPolicy.DESTROY,
        )

        # Block insecure requests to the bucket
        s3_artifact.add_to_resource_policy(
            iam.PolicyStatement(
                sid="AllowSSLRequestsOnly",
                actions=["s3:*"],
                effect=iam.Effect.DENY,
                resources=[
                    s3_artifact.bucket_arn,
                    s3_artifact.arn_for_objects(key_pattern="*"),
                ],
                conditions={"Bool": {"aws:SecureTransport": "false"}},
                principals=[iam.AnyPrincipal()],
            )
        )

        s3_artifact.add_to_resource_policy(
            iam.PolicyStatement(
                sid="AddDevPermissions",
                actions=["s3:*"],
                resources=[
                    s3_artifact.arn_for_objects(key_pattern="*"),
                    s3_artifact.bucket_arn,
                ],
                principals=[
                    iam.ArnPrincipal(f"arn:aws:iam::{Aws.ACCOUNT_ID}:root"),
                    iam.ArnPrincipal(f"arn:aws:iam::{stg_account}:root"),
                    iam.ArnPrincipal(f"arn:aws:iam::{prod_account}:root"),

                ],
            )
        )

        # create the model package groups
        dev_model_package_group_name = f"{project_name}-{project_id}-dev"
        stg_model_package_group_name = f"{project_name}-{project_id}-stg"
        prod_model_package_group_name = f"{project_name}-{project_id}-prod"

        stg_model_package_group_policy = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    sid="ModelPackageGroup",
                    actions=[
                        "sagemaker:DescribeModelPackageGroup",
                    ],
                    resources=[
                        f"arn:aws:sagemaker:{Aws.REGION}:{Aws.ACCOUNT_ID}:model-package-group/{stg_model_package_group_name}"
                    ],
                    principals=[
                        iam.ArnPrincipal(f"arn:aws:iam::{stg_account}:root"),
                        iam.ArnPrincipal(f"arn:aws:iam::{Aws.ACCOUNT_ID}:root"),
                    ],
                ),
                iam.PolicyStatement(
                    sid="ModelPackage",
                    actions=[
                        "sagemaker:DescribeModelPackage",
                        "sagemaker:ListModelPackages",
                        "sagemaker:UpdateModelPackage",
                        "sagemaker:CreateModel",
                        "sagemaker:CreateModelPackage",

                    ],
                    resources=[
                        f"arn:aws:sagemaker:{Aws.REGION}:{Aws.ACCOUNT_ID}:model-package/{stg_model_package_group_name}/*"
                    ],
                    principals=[
                        iam.ArnPrincipal(f"arn:aws:iam::{stg_account}:root"),
                        iam.ArnPrincipal(f"arn:aws:iam::{Aws.ACCOUNT_ID}:root"),
                    ],
                ),
            ]
        ).to_json()
        
        prod_model_package_group_policy = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    sid="ModelPackageGroup",
                    actions=[
                        "sagemaker:DescribeModelPackageGroup",
                    ],
                    resources=[
                        f"arn:aws:sagemaker:{Aws.REGION}:{Aws.ACCOUNT_ID}:model-package-group/{prod_model_package_group_name}"
                    ],
                    principals=[
                        iam.ArnPrincipal(f"arn:aws:iam::{prod_account}:root"),
                        iam.ArnPrincipal(f"arn:aws:iam::{Aws.ACCOUNT_ID}:root"),
                    ],
                ),
                iam.PolicyStatement(
                    sid="ModelPackage",
                    actions=[
                        "sagemaker:DescribeModelPackage",
                        "sagemaker:ListModelPackages",
                        "sagemaker:UpdateModelPackage",
                        "sagemaker:CreateModel",
                        "sagemaker:CreateModelPackage",
                    ],
                    resources=[
                        f"arn:aws:sagemaker:{Aws.REGION}:{Aws.ACCOUNT_ID}:model-package/{prod_model_package_group_name}/*"
                    ],
                    principals=[
                        iam.ArnPrincipal(f"arn:aws:iam::{prod_account}:root"),
                        iam.ArnPrincipal(f"arn:aws:iam::{Aws.ACCOUNT_ID}:root"),
                    ],
                ),
            ]
        ).to_json()
        

        dev_model_package_group = sagemaker.CfnModelPackageGroup(
            self,
            "ModelPackageGroupDev",
            model_package_group_name=dev_model_package_group_name,
            model_package_group_description=f"Model Package Group for {project_name}",
            # model_package_group_policy=model_package_group_policy,
            tags=[
                aws_cdk.CfnTag(key="sagemaker:project-id", value=project_id),
                aws_cdk.CfnTag(key="sagemaker:project-name", value=project_name),
            ],
        )

        stg_model_package_group = sagemaker.CfnModelPackageGroup(
            self,
            "ModelPackageGroupStg",
            model_package_group_name=stg_model_package_group_name,
            model_package_group_description=f"Model Package Group for {project_name}",
            model_package_group_policy=stg_model_package_group_policy,
            tags=[
                aws_cdk.CfnTag(key="sagemaker:project-id", value=project_id),
                aws_cdk.CfnTag(key="sagemaker:project-name", value=project_name),
            ],
        )

        prod_model_package_group = sagemaker.CfnModelPackageGroup(
            self,
            "ModelPackageGroupProd",
            model_package_group_name=prod_model_package_group_name,
            model_package_group_description=f"Model Package Group for {project_name}",
            model_package_group_policy=prod_model_package_group_policy,
            tags=[
                aws_cdk.CfnTag(key="sagemaker:project-id", value=project_id),
                aws_cdk.CfnTag(key="sagemaker:project-name", value=project_name),
            ],
        )


        # create the repositories
        path = Path(__file__)

        # deploy repo
        deploy_asset = s3_assets.Asset(
            self,
            "DeployAsset",
            path=os.path.join(os.path.abspath(path.parent), "seed_code/deploy_app"),
            bundling=BundlingOptions(
                image=DockerImage.from_build(
                    os.path.join(os.path.abspath(path.parent.parent), "cdk_helper_scripts/zip-image")
                ),
                command=[
                    "sh",
                    "-c",
                    """zip -r /asset-output/deploy_app.zip . -x "*.git*" -x "*cdk.out*"  -x "*.DS_Store*" """,
                ],
                output_type=BundlingOutput.ARCHIVED,
            ),
        )

        deploy_app_cfnrepository = codecommit.CfnRepository(
            self,
            "DeployAppCodeRepo",
            repository_name=f"deploy-{project_name}-{project_id}",
            code=codecommit.CfnRepository.CodeProperty(
                s3=codecommit.CfnRepository.S3Property(
                    bucket=deploy_asset.s3_bucket_name,
                    key=deploy_asset.s3_object_key,
                    object_version=None,
                ),
                branch_name="main",
            ),
            tags=[
                aws_cdk.CfnTag(key="sagemaker:project-id", value=project_id),
                aws_cdk.CfnTag(key="sagemaker:project-name", value=project_name),
            ],
        )   

        deploy_app_repository = codecommit.Repository.from_repository_name(
            self, "DeployRepo", f"deploy-{project_name}-{project_id}"
        )

        # build repo 
        build_asset = s3_assets.Asset(
            self,
            "BuildAsset",
            path=os.path.join(os.path.abspath(path.parent), "seed_code/build_app"),
            bundling=BundlingOptions(
                image=DockerImage.from_build(
                    os.path.join(os.path.abspath(path.parent.parent), "cdk_helper_scripts/zip-image")
                ),
                command=[
                    "sh",
                    "-c",
                    """zip -r /asset-output/build_app.zip . -x "*.git*" -x "*cdk.out*"  -x "*.DS_Store*" """,
                ],
                output_type=BundlingOutput.ARCHIVED,
            ),
        )

        build_app_cfnrepository = codecommit.CfnRepository(
            self,
            "BuildAppCodeRepo",
            repository_name=f"build-{project_name}-{project_id}",
            code=codecommit.CfnRepository.CodeProperty(
                s3=codecommit.CfnRepository.S3Property(
                    bucket=build_asset.s3_bucket_name,
                    key=build_asset.s3_object_key,
                    object_version=None,
                ),
                branch_name="main",
            ),
            tags=[
                aws_cdk.CfnTag(key="sagemaker:project-id", value=project_id),
                aws_cdk.CfnTag(key="sagemaker:project-name", value=project_name),
            ],
        )   

        build_app_repository = codecommit.Repository.from_repository_name(
            self, "BuildRepo", f"build-{project_name}-{project_id}"
        )

        ######## deploy pipelines ########
        cdk_synth_build_role = iam.Role(
            self,
            "CodeBuildRole",
            assumed_by=iam.ServicePrincipal("codebuild.amazonaws.com"),
            path="/service-role/",
        )

        cdk_synth_build_role.add_to_policy(
            iam.PolicyStatement(
                actions=["sagemaker:ListModelPackages"],
                resources=[
                    f"arn:{Aws.PARTITION}:sagemaker:{Aws.REGION}:{Aws.ACCOUNT_ID}:model-package-group/{project_name}-{project_id}*",
                    f"arn:{Aws.PARTITION}:sagemaker:{Aws.REGION}:{Aws.ACCOUNT_ID}:model-package/{project_name}-{project_id}-*/*",
                ],
            )
        )

        cdk_synth_build_role.add_to_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter"],
                resources=[
                    f"arn:{Aws.PARTITION}:ssm:{Aws.REGION}:{Aws.ACCOUNT_ID}:parameter/*",
                ],
            )
        )

        cdk_synth_build_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "kms:Encrypt",
                    "kms:ReEncrypt*",
                    "kms:GenerateDataKey*",
                    "kms:Decrypt",
                    "kms:DescribeKey",
                ],
                effect=iam.Effect.ALLOW,
                resources=[f"arn:aws:kms:{Aws.REGION}:{Aws.ACCOUNT_ID}:key/*"],
            ),
        )

        DeployPipeline(
            self,
            project_id=project_id,
            project_name=project_name,
            construct_id=construct_id,
            env_name='dev',
            account_id=dev_account,
            model_package_group_name=dev_model_package_group_name,
            s3_artifact=s3_artifact,
            cdk_synth_build_role=cdk_synth_build_role,
            deploy_app_repository=deploy_app_repository
            )
        
        DeployPipeline(
            self,
            project_id=project_id,
            project_name=project_name,
            construct_id=construct_id,
            env_name='stg',
            account_id=stg_account,
            model_package_group_name=stg_model_package_group_name,
            s3_artifact=s3_artifact,
            cdk_synth_build_role=cdk_synth_build_role,
            deploy_app_repository=deploy_app_repository
            )
        
        DeployPipeline(
            self,
            project_id=project_id,
            project_name=project_name,
            construct_id=construct_id,
            env_name='prod',
            account_id=prod_account,
            model_package_group_name=prod_model_package_group_name,
            s3_artifact=s3_artifact,
            cdk_synth_build_role=cdk_synth_build_role,
            deploy_app_repository=deploy_app_repository
            )

        BuildPipeline(
            self, 
            project_name=project_name, 
            project_id=project_id, 
            construct_id=construct_id,
            s3_artifact=s3_artifact,
            build_app_repository=build_app_repository,
            stg_account=stg_account,
            prod_account=prod_account,
            dev_model_package_group_name=dev_model_package_group_name,
            stg_model_package_group_name=stg_model_package_group_name,
            prod_model_package_group_name=prod_model_package_group_name
            )

