# Basic Project Template

## Basic Project Stack
*This stack is stored as a service catalog product in the DEV Account and is visible in SageMaker Studio Domain*

![project architecture](../../diagrams/MLOPs%20Foundation%20Architecture-sagemaker%20project%20architecture.jpg)

The ML solutions' strategy defined in this stack uses two repositories setup: **(a)** building/training repository for training and batch inference ML pipeline development, and **(b)** deployment repository to promote the batch inference pipeline models or instantiate the real time endpoints. The second repository will incorporate also the testing methods including, integration test, stress test, or custom ML tests that the data scientists want to perform to ensure the robustness of the models.

The CI/CD pipelines follow a single branch strategy with deployments to the accounts driven by commits to the `main` branch. The pipeline contains a stage for each account deployment.

The stack expects 2 cloudformation parameters:
- **Project Name:** This parameter is of type `String` and is mandatory to be created for SageMaker Project. It will be visible in SageMaker Studio Domain and be used to then tag all the resources related to SageMaker and have them visible under the project tab. It must be named `SageMakerProjectName`.
- **Project ID:** This parameter is of type `String` and is mandatory to be created for SageMaker Project. When creating a project in SageMaker Studio Domain and it will be automatically generated and then used to tag all the resources related to SageMaker and have them visible under the project tab. It must be named `SageMakerProjectId`.

Other parameters can be included and those will be visible in SageMaker Studio Domain during Project Creation.

All resources deployed as part of this stack are tagged with those 2 parameters.

This stack can be broken into 3 parts:  
- **[Shared resources with Cross Account Permissions](#shared-resources)**
- **[Build application resources and CI/CD pipeline](#build-app-cicd-construct)**
- **[Deploy application resources and CI/CD pipeline](#deploy-app-cicd-construct)**  


### Shared Resources
The following resources are deployed as part of a SageMaker Project and are used by both build and deploy applications:
- **Artifact Bucket** and its **KMS key**, this bucket will be used to store SageMaker Pipeline's steps outputs and also the trained model for this project.
- **Model Package Group**, this group is created at this stack mainly to setup its policy and enable cross account access to the other deployment accounts.
- **Pipeline Bucket** and its **KMS key**, this bucket will be used by both CICD pipelines to store the pipelines artifacts.

These resources are deployed to the DEV account with cross account access enabled for PREPROD and PROD; except for the pipeline bucket and its kms key, those are constraint to the DEV account.

### Build App CI/CD Construct
*The CICD pipeline in this construct only deploys to DEV*
![build app](../../diagrams/building.png)

This construct contains resources that create a CI/CD pipeline to orchestrate a model training using SageMaker Pipelines starting from doing preprocessing jobs over the data and end by registering the trained model in a model package group in SageMaker Model Registry. After the pipeline finishes running successfuly, the model will have `Pending Manual Approval` status in SageMaker Model Registry.

In `seed_code/build_app`, you will find the base code that would be setup when you create a new SageMaker Project. It is **python** based and is expected to run inside a CodeBuild project. There is a `buildspec.yml` that describes the command that will be run. For more details about this base code, refer to `seed_code/build_app/README.md`.

The following resources are created in this construct:
- **CodeCommit Repository**, this repository is intialised with the code defined in `seed_code/build_app` which was the stored in an S3 bucket when the service catalog stack was deployed. The s3 bucket name and code zip key are stored in ssm parameters: `/mlops/code/seed_bucket` and `/mlops/code/build`. The stack expects these parameters to exist in the account.
- **CodeBuild Project**, this codebuild project is used to create/update/run the SageMaker Pipeline defined in the **build app repository** in `ml_pipelines/training/pipeline.py`. The project's **buildspec** uses the `buildspec.yml` defined in the repository as well.
- **CodePipeline Pipeline**, this pipeline has the **CodeCommit Repository** created in this construct as source and monitors the commits to the **main** branch. It has one additional stage, **Build** stage, which runs the **CodeBuild Project** defined above.

**NOTE** The solution defined above only support a CICD pipeline that is linked to the **main** branch update events. If you want to have a **multi-branch approach** i.e. a CI/CD pipeline linked to the **develop** then you will need to duplicate the exisiting pipeline and ensure resources for each branch are **isolated** to not have impact on each other. You will also need to recosider the prefix strategy used in **Artifact Bucket**, created in [shared resources section](#shared-resources).



### Deploy App CI/CD Construct
*The CICD pipeline in this construct only deploy to DEV, PREPROD and PROD*
![build app](../../diagrams/deployment.png)

This construct contains resources that create a CI/CD pipeline to automate the deployment of an Amazon SageMaker Endpoint for real time inference across multiple accounts.

In `seed_code/deploy_app`, you will find the base code that would be setup when you create a new SageMaker Project. It is **python** based **AWS CDK** application. For more details about this base code, refer to `seed_code/deploy_app/README.md`.


The following resources are created in this construct:
- **CodeCommit Repository**, this repository is intialised with the code defined in `seed_code/deploy_app` which was the stored in an S3 bucket when the service catalog stack was deployed. The s3 bucket name and code zip key are stored in ssm parameters: `/mlops/code/seed_bucket` and `/mlops/code/deploy`. The stack expects these parameters to exist in the account.
- **EventBridge Rule**, this rule is linked to the model package group used for this SageMaker Project. It will be monitoring **Approved** and **Rejected** events and will trigger the deployment CI/CD pipeline on them.
- **CodeBuild Project for CDK Synth**, this codebuild project is used to synthesize the AWS CDK application defined in the **deploy app repository**. 3 Cloudformation Templates are expected to be generated, each template references a targeted deployment account/environment: DEV, PREPROD and PROD.
- **CodeBuild Project for CFN Nag**, this codebuild project is used to run `cfn-nag` over the cloudformation templates to ensure that they satisfy best Security practices.
- **CodePipeline Pipeline**, this pipeline has the **CodeCommit Repository** created in this construct as source and monitors the commits to the **main** branch. The stages for this pipeline are defined as such:
  - A **Build** stage which runs the **CodeBuild Project for CDK Synth**
  - A **Security Evaluation** stage which runs the **CodeBuild Project for CFN Nag**
  - There is a stage for each account: **DEV**, **PREPROD** and **PROD** each using Cloudformation Action to deploy the templates generated in the **Build** stage. There is a manual approval action before **PREPROD** and **PROD** deployments.

There are 2 way to trigger the deployment CI/CD Pipeline:
- **Model Events** - These are events which get triggered through a status change to the model package group in SageMaker Model Registry.
- **Code Events** - The pipeline is triggered on git update events over a specific branch, in this solution it is linked to the **main** branch.

**Note:** For the deployment stages for **PREPROD** and **PROD**, the roles defined for cloudformation deployment in `mlops_sm_project_template/templates/constructs/deploy_pipeline_construct.py` lines 284-292 and lines 317-326 are created when the **PREPROD** and **PROD** are bootstrapped with CDK with trust policies for the deployment CI/CD pipeline account (**DEV** account in our solution); the roles must be created before deploying this stack to any account along with trust policies included between the accounts and the roles. If you can bootstrap those accounts for any reason you should ensure to create similar roles in each of those accounts and adding them to the lines mentioned above in the file.
