# Developer Guide
While the solution presented in [README](README.md) can be used as is, this repository is built with the intention to be customized for the need of your organization.

[mlops-sm-project-template](mlops-sm-project-template/) will:
- Create a Service Catalogue Portfolio via [service_catalog_stack](mlops-sm-project-template/service_catalog_stack.py).
- Create SageMaker Project Templates (Service Catalog Products) inside the Service Catalogue Portfolio. Each SageMaker Project template is a CDK stack called `MLOpsStack` inside [templates](mlops_sm_project_template/templates/)

The high level design of each of those SageMaker Project Templates as described in [README](README.md) is the same:
- Two CodeCommit repositories (one for `build` and one for `deploy`) instantiated with their respective seed code found in [seed_code](mlops_sm_project_template/seed_code/)
- Two CodePipelines linked to the respective repositories, whose definitions are provided as CDK Constructs under [pipeline_constructs](mlops_sm_project_template/templates/pipeline_constructs) or [byoc_pipelines_constructs](mlops_sm_project_template/templates/byoc_pipeline_constructs/)

By default, if changes to the `build` or `deploy` repositories of a project are specific to a use case (work done by Data Scientists), we do not recommend changing seed codes.
However if you observe repeated patterns that you want to make available accross your organization, for example:
- You see many projects that would benefit from having an example SageMaker Processing step querying Amazon Athena
- You want a project that provides an example to train and deploy an LLM (Large Language Model)
- You want a project to deploy not just an endpoint but for example an API Gateway and a Lambda function
Then you could either modify an existing [template project stack](mlops_sm_project_template/templates/) or create your own.

If you want to create a new Service Catalogue Product / SageMaker Project template in the Service Catalogue Portfolio, you should:
- Create a new `*_project_stack.py` in [templates](mlops_sm_project_template/templates/) (you can copy a pre-existing one such as [dynamic_accounts_project_stack](mlops_sm_project_template/templates/dynamic_accounts_project_stack.py))
- You can reuse existing or create new CICD pipeline constructs in as in [pipeline_constructs](mlops_sm_project_template/templates/pipeline_constructs)
- You can provide your own `seed_code` for either the build or deploy app or both. Your `YOUR_CUSTOM_project_stack.py` should reference to the new ones you created.

By default a SageMaker Project Template contains two repositories (but you can change that based on your organization's requirements). The definitions of those repositories are contained in [seed_code](mlops_sm_project_template/seed_code/).
The [service_catalog_stack](mlops-sm-project-template/service_catalog_stack.py) packages the content of the subfolders in s3 via `aws_cdk.aws_s3_assets.s3_assets.Asset()` and shares the s3 key via SSM.

For example:

```
        build_app_asset = s3_assets.Asset(
            self,
            "BuildAsset",
            path="seed_code/build_app/",
            ...
        )
```

```
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
```

Whenever a SageMaker Project Template is instantiated by a user, the CodeCommit repositories will be initially populated with the seed code provided as s3_assets.
The SSM paths containing the s3 paths of the seed repositories are passed as arguments to the CICD pipeline constructs (eg [build_pipeline_construct](mlops_sm_project_template/templates/pipeline_constructs/build_pipeline_construct.py) which are in charge or creating the CodeCommit repositories and respective Code Pipelines.

For example in [dynamic_accounts_project_stack](mlops_sm_project_template/templates/dynamic_accounts_project_stack.py):

```
        seed_bucket = CfnDynamicReference(CfnDynamicReferenceService.SSM, "/mlops/code/seed_bucket").to_string()
        build_app_key = CfnDynamicReference(CfnDynamicReferenceService.SSM, "/mlops/code/build").to_string()
        deploy_app_key = CfnDynamicReference(CfnDynamicReferenceService.SSM, "/mlops/code/deploy").to_string()
```
and
```
        BuildPipelineConstruct(
            self,
            "build",
            project_name,
            project_id,
            s3_artifact,
            pipeline_artifact_bucket,
            model_package_group_name,
            seed_bucket,        <--- SSM path or s3 path passed above
            build_app_key,      <--- SSM path or s3 path passed above
        )
```

Note: if you plan on deploying directly an `MLOpsStack` (from a `*_project_stack.py`), without going through Service Catalogue Portfolio, using `cdk deploy`, you can pass the s3 location of your seed code directly.
The mechanism of Service Catalogue Portfolio helps automating the maintenance of custom SageMaker Project templates that your organization makes available to their data scientists in target accounts.

## Modifying / creating new seed code
For example if you would like to create a new `build` seed code for model training you would create a new subfolder containing your example `build` code in [seed_code](mlops_sm_project_template/seed_code).
Then you would modify [service_catalog_stack](mlops-sm-project-template/service_catalog_stack.py) to create a new s3 asset for that code and publish it to SSM.
Then you would create a new [*_project_stack.py](mlops-sm-project-template/templates/) where the `build` pipeline creates a `aws_cdk.aws_codecommit.codecommit()` refering to your new seed code.

```
└── seed_code                                 <--- code samples to be used to setup the build and deploy repositories of the sagemaker project
    ├── build_app
    ├── deploy_app
    └── llm_build_app                         <--- new build app / seed code
```

inside [service_catalog_stack](mlops-sm-project-template/service_catalog_stack.py):

```
        llm_build_app_asset = s3_assets.Asset(
            self,
            "LLMBuildAsset",
            path="seed_code/llm_build_app/",
            ...
        )
```
and
```
        self.export_ssm(
            "CodeBuildKey",
            "/mlops/code/llm_build",
            llm_build_app_asset.s3_object_key,
        )
```

and then inside your new [*_project_stack.py](mlops-sm-project-template/templates/) passing
```
        build_app_key = CfnDynamicReference(CfnDynamicReferenceService.SSM, "/mlops/code/llm_build").to_string()
```
```
        BuildPipelineConstruct(
            self,
            "build",
            ...
            build_app_key,      <--- SSM path or s3 path passed above
        )
```

## Modifying / creating new CICD Pipelines (CodePipeline)
For example if you would like to create or modify a template to have different CICD pipelines definitions (eg adding you own linter checks, organization specific integration tests, etc).
You would either create a new or modify an existing [*_project_stack.py](mlops-sm-project-template/templates/) and its associated [pipeline_constructs](mlops_sm_project_template/templates/pipeline_constructs/).

Here is a dummy example adding a manual approval after running a SageMaker Pipeline in the `build` CICD Pipeline:

Inside [build_pipeline_construct](mlops_sm_project_template/templates/pipeline_constructs/build_pipeline_construct.py) you would change:

```
        # add a build stage
        build_stage = build_pipeline.add_stage(stage_name="Build")
        build_stage.add_action(
            codepipeline_actions.CodeBuildAction(
                action_name="SMPipeline",
                input=source_artifact,
                project=sm_pipeline_build,
            )
        )
```
to instead be:

```
        # add a build stage
        build_stage = build_pipeline.add_stage(
            stage_name="Build",
            actions=[
                codepipeline_actions.CodeBuildAction(
                    action_name="SMPipeline",
                    input=source_artifact,
                    project=sm_pipeline_build,
                    run_order=1,
                ),
                codepipeline_actions.ManualApprovalAction(
                    action_name="Manual_Approval",
                    run_order=2,
                    additional_information="Manual Approval to confirm SM Pipeline ran successfuly",
                ),
            ]
```


Here is another example changing the cross account roles that the `deploy` pipeline(s) use to execute CloudFormation in your PREPROD/PROD accounts. In the `deploy` CICD Pipeline:

Inside [deploy_pipeline_construct](mlops_sm_project_template/templates/pipeline_constructs/deploy_pipeline_construct.py) you would change:

```
        deploy_code_pipeline.add_stage(
            stage_name="DeployPreProd",
            actions=[
                codepipeline_actions.CloudFormationCreateUpdateStackAction(
                    action_name="Deploy_CFN_PreProd",
                    ...
                    role=iam.Role.from_role_arn(
                        self,
                        "PreProdActionRole",
                        f"arn:{Aws.PARTITION}:iam::{preprod_account}:role/cdk-hnb659fds-deploy-role-{preprod_account}-{deployment_region}",     <--- This role is currently created via doing cdk bootstrap in the target accounts
                    ),
                    deployment_role=iam.Role.from_role_arn(
                        self,
                        "PreProdDeploymentRole",
                        f"arn:{Aws.PARTITION}:iam::{preprod_account}:role/cdk-hnb659fds-cfn-exec-role-{preprod_account}-{deployment_region}",   <--- This role is currently created via doing cdk bootstrap in the target accounts
                    ),
                    ...
                ),
                ...
            ],
        )
```
to
```
        deploy_code_pipeline.add_stage(
            stage_name="DeployPreProd",
            actions=[
                codepipeline_actions.CloudFormationCreateUpdateStackAction(
                    action_name="Deploy_CFN_PreProd",
                    ...
                    role=iam.Role.from_role_arn(
                        self,
                        "PreProdActionRole",
                        f"{PARAMETRIZED_ARN_OF_YOUR_CROSS_ACCOUNT_ACTION_ROLE}",   <--- Role to be changed here
                    ),
                    deployment_role=iam.Role.from_role_arn(
                        self,
                        "PreProdDeploymentRole",
                        f"{PARAMETRIZED_ARN_OF_YOUR_CROSS_ACCOUNT_DEPLOY_ROLE},    <--- Role to be changed here
                    ),
                    ...
                ),
                ...
            ],
        )
```