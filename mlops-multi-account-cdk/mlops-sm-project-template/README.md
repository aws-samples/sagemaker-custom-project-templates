# MLOps Foundation SageMaker Project Template
This repository contains the resources that are required to deploy the MLOps Foundation SageMaker Project Template.

- [MLOps Foundation SageMaker Project Template](#mlops-foundation-sagemaker-project-template)
  - [Solution Architecture](#solution-architecture)
    - [Service Catalog Stack](#service-catalog-stack)
    - [SageMaker Project Stack](#sagemaker-project-stack)
      - [Shared Resources](#shared-resources)
      - [Build App CI/CD Construct](#build-app-cicd-construct)
      - [Deploy App CI/CD Construct](#deploy-app-cicd-construct)
    - [CodeCommit Stack](#codecommit-stack)
    - [Pipeline Stack](#pipeline-stack)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Repository Structure](#repository-structure)
    - [Setup AWS Profiles](#setup-aws-profiles)
    - [Bootstrap AWS Accounts](#bootstrap-aws-accounts)
    - [Deployment Options](#deployment-options)
      - [CI/CD Deployment of Service Catalog Stack](#cicd-deployment-of-service-catalog-stack)
      - [Manual Deployment of Service Catalog Stack](#manual-deployment-of-service-catalog-stack)
    - [Clean-up](#clean-up)
  - [Troubleshooting](#troubleshooting)

## Solution Architecture

![mlops project architecture](diagrams/MLOPs%20Foundation%20Architecture-mlops%20project%20cicd%20architecture.jpg)


### Service Catalog Stack

*This stack is only deployed in the DEV account*

In this stack we define the Service Catalog Portfolio and Product that we want to use for SageMaker Project Template.

The stack expects 4 cloudformation parameters:
- **Execution Role Arn:** This parameter is of type `AWS::SSM::Parameter::Value<String>` so you should provide an `SSM Parameter Name` as an input; the default value is `"/mlops/role/lead"` which is deployed as part of **mlops infrastructure repository**. Ensure you have this parameter defined in your account before you deploy the solution. This is the role that would be given visibility to the Service Catalog Portfolio and Products. Products with tag `sagemaker:studio-visibility = true` will be visible in SageMaker Studio Domain.
- **Portfolio Name:** This parameter is of type `String` and has a default value of `SageMaker Organization Templates`. It will be used for Service Catalog Portfolio resource.
- **Portfolio Owner:** This parameter is of type `String` and has a default value of `administrator`. It will be used for Service Catalog Portfolio and Product resources.
- **Product Version:** This parameter is of type `String` and has a default value of `1.0`. It will be used for Service Catalog Product resource.

The following resources are created:
- **Product Launch Role** is created which has permissions to create all the resources defined in SageMaker Project Stack and access to resources used in that stack i.e. SSM Parameters and access to CDK Assets S3 bucket (deployed as part of CDKToolkit stack).
- **A Service Catalog Product**, CloudFormation Product, for SageMaker Project Template as defined in [SageMaker Project Stack](#sagemaker-project-stack). The Product Launch Role is linked to this product.
- **A Service Catalog Portfolio**, the product would be associated to this portfolio and has visibility to sagemaker studio and linked to the Execution Role provided in the cloudformation parameters.
- **2 assets**, a zip for the **seed code** for each of the **build app** and the **deploy app**, stored in CDK Assets bucket, this bucket is created as part of **CDKToolkit stack**. A SSM Parameter is created for each asset's s3 key and also for the s3 bucket name. These parameters are used in [SageMaker Project Stack](#sagemaker-project-stack). The assets structure is documented in [MLOps Foundation Strategy](link-quip)
- **SSM Parameters** containig configuration about the target deployment accounts: **DEV**, **PREPROD** and **PROD** i.e. account id, region. These Parameters are used by the deploy app.

Once this stack is deployed in the account, the template will be usable by Amazon SageMaker Studio Domain user with the role: **Execution Role** that was provided to this stack.


### SageMaker Project Stack
*This stack is stored as a service catalog product in the DEV Account and is visible in SageMaker Studio Domain*

![project architecture](diagrams/MLOPs%20Foundation%20Architecture-sagemaker%20project%20architecture.jpg)

The ML solutions' strategy defined in this stack uses two repositories setup: **(a)** building/training repository for training and batch inference ML pipeline development, and **(b)** deployment repository to promote the batch inference pipeline models or instantiate the real time endpoints. The second repository will incorporate also the testing methods including, integration test, stress test, or custom ML tests that the data scientists want to perform to ensure the robustness of the models.

The CI/CD pipelines follow a single branch strategy with deployments to the accounts driven by commits to the `main` branch. The pipeline contains a stage for each account deployment.

The stack expects 2 cloudformation parameters:
- **Project Name:** This parameter is of type `String` and is mandatory to be created for SageMaker Project. It will be visible in SageMaker Studio Domain and be used to then tag all the resources related to SageMaker and have them visible under the project tab. It must be named `SageMakerProjectName`.
- **Project ID:** This parameter is of type `String` and is mandatory to be created for SageMaker Project. When creating a project in SageMaker Studio Domain and it will be automatically generated and then used to tag all the resources related to SageMaker and have them visible under the project tab. It must be named `SageMakerProjectId`.

Other parameters can be included and those will be visible in SageMaker Studio Domain during Project Creation.

All resources deployed as part of this stack are tagged with those 2 parameters.

This stack can be broken into 3 parts:
- [Shared resources with Cross Account Permissions](#shared-resources)
- [Build application resources and CI/CD pipline](#build-app-cicd-construct)
- [Deploy application resources and CI/CD pipeline](#deploy-app-cicd-construct)

#### Shared Resources
The following resources are deployed as part of a SageMaker Project and are used by both build and deploy applications:
- **Artifact Bucket** and its **KMS key**, this bucket will be used to store SageMaker Pipeline's steps outputs and also the trained model for this project.
- **Model Package Group**, this group is created at this stack mainly to setup its policy and enable cross account access to the other deployment accounts.
- **Pipeline Bucket** and its **KMS key**, this bucket will be used by both CICD pipelines to store the pipelines artifacts.

These resources are deployed to the DEV account with cross account access enabled for PREPROD and PROD; except for the pipeline bucket and its kms key, those are constraint to the DEV account.

#### Build App CI/CD Construct
*The CICD pipeline in this construct only deploys to DEV*
![build app](diagrams/building.png)

This construct contains resources that create a CI/CD pipeline to orchestrate a model training using SageMaker Pipelines starting from doing preprocessing jobs over the data and end by registering the trained model in a model package group in SageMaker Model Registry. After the pipeline finishes running successfuly, the model will have `Pending Manual Approval` status in SageMaker Model Registry.

In `seed_code/build_app`, you will find the base code that would be setup when you create a new SageMaker Project. It is **python** based and is expected to run inside a CodeBuild project. There is a `buildspec.yml` that describes the command that will be run. For more details about this base code, refer to `seed_code/build_app/README.md`.

The following resources are created in this construct:
- **CodeCommit Repository**, this repository is intialised with the code defined in `seed_code/build_app` which was the stored in an S3 bucket when the service catalog stack was deployed. The s3 bucket name and code zip key are stored in ssm parameters: `/mlops/code/seed_bucket` and `/mlops/code/build`. The stack expects these parameters to exist in the account.
- **CodeBuild Project**, this codebuild project is used to create/update/run the SageMaker Pipeline defined in the **build app repository** in `ml_pipelines/training/pipeline.py`. The project's **buildspec** uses the `buildspec.yml` defined in the repository as well.
- **CodePipeline Pipeline**, this pipeline has the **CodeCommit Repository** created in this construct as source and monitors the commits to the **main** branch. It has one additional stage, **Build** stage, which runs the **CodeBuild Project** defined above.

**NOTE** The solution defined above only support a CICD pipeline that is linked to the **main** branch update events. If you want to have a **multi-branch approach** i.e. a CI/CD pipeline linked to the **develop** then you will need to duplicate the exisiting pipeline and ensure resources for each branch are **isolated** to not have impact on each other. You will also need to recosider the prefix strategy used in **Artifact Bucket**, created in [shared resources section](#shared-resources).



#### Deploy App CI/CD Construct
*The CICD pipeline in this construct only deploy to DEV, PREPROD and PROD*
![build app](diagrams/deployment.png)

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

### CodeCommit Stack
*This stack is only needed if you want to handle deployments of this folder of the repository to be managed through a CICD pipeline.*

This stack handles setting up an AWS CodeCommit repository for this folder of the repository. This repository will be used as the source for the CI/CD pipeline defined in [Pipeline Stack](#pipeline-stack). The repository will be named based on the value defined in `mlops_sm_project_template/config/constants.py` with this variable `CODE_COMMIT_REPO_NAME`. The repository will be intialised with a default branch as defined in the `constants.py` file under `PIPELINE_BRANCH` variable.

### Pipeline Stack

*This stack is only needed if you want to handle deployments of this folder of repository to be managed through a CICD pipeline. The pipeline is configured to deploy to 1 account: DEV and will deploy the service catalog stack to the target account*

The CICD pipeline in this repository is setup to monitor an AWS CodeCommit repository as defined in [CodeCommit Stack](#codecommit-stack).

If you are using other sources like github or bitbucket for your repository, you will need to modify the connection to the appropriate repository as defined in `mlops_sm_project_template/pipeline_stack.py`. This can be done using AWS CodeStar but must be setup on the account.

Make sure the pipelines also point to your targeted branch; by default the pipeline is linked to `main` branch events, this is defined in the `constants.py` file under `PIPELINE_BRANCH` variable.

`constants.py` also contains information about the target accounts you want to use for this repository CI/CD pipeline and the target deployment accounts: **DEV**, **PREPROD** and **PROD**, this information will also be deployed in SSM Parameter in the DEV account for the Deploy App CI/CD pipeline.

The pipeline will deploy all stacks and resources to the appropriate accounts.


## Getting Started

### Prerequisites

This is an AWS CDK project written in Python 3.8. Here's what you need to have on your workstation before you can deploy this project. It is preferred to use a linux OS to be able to run all cli commands and avoid path issues.

* [Node.js](https://nodejs.org/)
* [Python3.8](https://www.python.org/downloads/release/python-380/) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
* [AWS CDK v2](https://aws.amazon.com/cdk/)
* [AWS CLI](https://aws.amazon.com/cli/)
* [Docker](https://docs.docker.com/desktop/)

### Repository Structure

```
.
├── LICENSE.txt
├── Makefile
├── README.md
├── app.py
├── cdk.json
├── diagrams
├── mlops_sm_project_template
│   ├── README.md
│   ├── __init__.py
│   ├── cdk_helper_scripts
│   ├── config
│   │   └── constants.py                      <--- global configs to be used in CDK stacks
│   ├── codecommit_stack.py                   <--- stack for creation a codecommit repo based on this folder for the CICD pipeline
│   ├── pipeline_stack.py                     <--- stack for CICD with code pipeline setup for the repo
│   ├── service_catalog_stack.py              <--- stack for service catalog setup and template deployment
│   ├── ssm_construct.py                      <--- construct to deploy ssm parameter for the project template to use
│   └── templates
│       ├── basic_project_stack.py                <--- stack for basic sagemaker project template setup - DEV/PREPROD/PROD Accounts provided in constants.py
│       ├── dynamic_accounts_project_stack.py     <--- stack for sagemaker project template setup - DEV/PREPROD/PROD Accounts provided as parameters during project creation
│       └── pipeline_constructs
│           ├── build_pipeline_construct.py       <--- construct containing CI/CD pipeline linked to the build app
│           └── deploy_pipeline_construct.py      <--- construct containing CI/CD pipeline linked to the deploy app
├── requirements-dev.txt
├── requirements.txt                          <--- cdk packages used in the stacks (must be installed)
├── scripts                                   <--- shell scripts to automate part of the deployments
│   ├── cdk-account-setup.sh
│   └── install-prerequisites-brew.sh
└── seed_code                                 <--- code samples to be used to setup the build and deploy repositories of the sagemaker project
    ├── build_app
    └── deploy_app
```

if you are using a mac or a linux machine that supports `make` commands, you will be able to do the following:

* use `make init` to setup githooks to manage commit for this repository. This will add some helper functionalities when ever you run `git commit` to format the code, add necessary headers, and also clears any jupyter notebooks.
* use `make clean` to clear out the repo from python specific cached resources.

This repository also contains some shell scripts that you can use to setup your machine and aws accounts:

* If you have a mac machine with [Homebrew](https://brew.sh/) installed, you can use `scripts/install-prerequisites-brew.sh` to install the prerequisites and setup the python environment

### Setup AWS Profiles

As the MLOps foundation is based on multiple accounts, it is necessary to create a simple way to interact with multiple AWS credentials. We recommend the creation of an AWS profile per account with enough permission to deploy to CloudFormation following the instructions [here](https://docs.aws.amazon.com/toolkit-for-visual-studio/latest/user-guide/keys-profiles-credentials.html#adding-a-profile-to-the-aws-credentials-profile-file) . For example, the `.aws/credentials` should look like:

```
[mlops-governance]
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
aws_session_token = YOUR_SESSION_TOKEN  # this token is generated if you are using an IAM Role to assume into the account

[mlops-dev]
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
aws_session_token = YOUR_SESSION_TOKEN  # this token is generated if you are using an IAM Role to assume into the account

[mlops-preprod]
...

[mlops-prod]
...
```

Before you start with the deployment of the solution make sure to bootstrap your accounts. Ensure you add the account details in `mlops_sm_project_template/config/constants.py` mainly the target deployment accounts: **DEV**, **PREPROD** and **PROD**.
```
PIPELINE_ACCOUNT = ""     # account to host the pipeline handling updates of this repository

DEV_ACCOUNT = ""          # account to host the service catalog template and then build sagemaker project

PREPROD_ACCOUNT = ""      # account to deploy the sagemaker endpoint

PROD_ACCOUNT = ""         # account to deploy the sagemaker endpoint
```


### Bootstrap AWS Accounts
***Warning:** It is best you setup a python environment to handle all installs for this project and manage python packages. Use your preferred terminal and editor to run the following commands.*

follow the steps below to achieve that:

1. Clone this repository in your work environment (e.g. your laptop)

2. Change directory to `mlops-sm-project-template-rt` root

```
cd mlops-sm-project-template-rt
```

3. Install dependencies in a separate python environment using your favourite python packages manager. You can refer to `scripts/install-prerequisites-brew.sh` for commands to setup a python environment.

```
 pip install -r requirements.txt
```

4. Run `make init` to setup githooks

5. Ensure your docker daemon is running

6. (Option 1) Bootstrap your deployment target accounts (e.g. governance, dev, etc.) using our script in `scripts/cdk-account-setup.sh.` Ensure that you have the account ids ready and the corresponding AWS profiles with credentials created in your `~/.aws/credentials` for each account (see above).

The script will request the 4 accounts, i.e. governance, dev, preprod and prod, and the corresponding AWS profiles as inputs. If you want to only deploy to 1 account you can use the same id for all account variables or pass the same values in the script.


6. (Option 2) If you want to bootstrap the account manually, then run the following command for each account:

```
cdk bootstrap aws://<target account id>/<target region> --profile <target account profile>
```

The bootstrap stack needs only to be deployed for the first time. Once deployed, the bootstrap will be updated as part of the pipeline's regular execution. You only need to deploy bootstrap into new target accounts you plan to add to the pipeline. (in case you get an error regarding CDK version not matching run the bootstrap command again after you have locally updated your cdk) for cross account deployment setup, run the following command. This is a one time operation for each target account we want to deploy.

```
cdk bootstrap aws://<target account id>/<target region> --trust <deployment account> --cloudformation-execution-policies <policies arn that you would allow the deployment account to use> --profile <target account profile>
```

The following is an example of the cloud formation execution policy:

```
--cloudformation-execution-policies `'arn:aws:iam::aws:policy/AdministratorAccess'`
```

for more information read the [AWS CDK documentation on Bootstrapping](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html#bootstrapping-howto)

### Deployment Options

***Warning:** It is best you setup a python environment to handle all installs for this project and manage python packages. Use your preferred terminal and editor to run the following commands.*

There are two deployment options for the SageMaker Project Template to the Service Catalog in the target account:

- **[CI/CD Deployment of Service Catalog Stack](#cicd-deployment-of-service-catalog-stack)** - deploy by using a governance account setup and a CICD pipeline linked to this folder of the repository

- **[Manual Deployment of Service Catalog Stack](#manual-deployment-of-service-catalog-stack)** - deploy without a governance account setup and directly to the targeted accounts (1 or more) using CDK commands


#### CI/CD Deployment of Service Catalog Stack
This step will deploy 2 stacks: [CodeCommit Stack](#codecommit-stack) and [Pipeline Stack](#pipeline-stack)

1. Deploy the deployment CI/CD pipeline in your governance account (one time operation). This is the CI/CD pipeline that would deploy your project template to Service Catalog in your dev account for the data science team to use:

```
# builds the pipeline stack and install all assets
cdk synth
# deploy stack to target account, use the governance account profile for this
cdk deploy --all --profile mlops-governance
```

2. the deployment CI/CD pipeline will now handle all deployments for the other stacks based on the updates to the main branch

#### Manual Deployment of Service Catalog Stack

It is possible to deploy a specific stage (in `pipeline_stack.py` refer to classes inheriting `Stage` class from `aws_cdk`). The same is possible to a singular stack (follow the same deployment steps as the pipeline stack).  `CoreStage` is a stage defined in `pipeline_stack.py` which contains the `ServiceCatalogStack` and is what the CI/CD pipeline deploys at every deployment stage to the target account of the stage. You can deploy this stage manually by following these steps:

1. Add a custom id to the target stage in `app.py`

```
# Personal Stacks for testing locally, comment out when committing to repository
CoreStage(
    app,
    "Personal",  ## change this to another stage name when doing local tests
    env=deployment_env,
)
```

2. Deploy the stage

```
cdk --app ./cdk.out/assembly-Personal deploy —all --profile mlops-dev
```

as a stage could include a combination of stacks `--all` flag is included with the `deploy` command


### Clean-up

In case you used the local deployment, once you are done with testing the new feature that was deployed locally, run the following commands to clean-up the environment:
```
# destroy stage to target account (make it match your stack name)
cdk --app ./cdk.out/assembly-Personal destroy —all --profile mlops-dev
```
This would only delete the service catalog stack deployed in the target account and not the deployed projects.

Similarly if you used the CI/CD deployment:
```
# destroy deployed stack in target account (make it match your stack name)
cdk destroy --all --profile mlops-governance
```
This would only delete the pipeline stack and nothing else deployed from the pipeline i.e. stacks deployed to the target accounts and the deployed projects.

This command could fail in the following cases:

* **S3 bucket not empty**

If you get this error just simply go to the console and empty the S3 bucket that caused the error and run the destroy command again.

* **Resource being used by another resource**

This error is harder to track and would require some effort to trace where is the resource that we want to delete is being used and severe that dependency before running the destroy command again.

**NOTE** You should just really follow CloudFormation error messages and debug from there as they would include details about which resource is causing the error and in some occasion information into what needs to happen in order to resolve it.

## Troubleshooting

* **CDK version X instead of Y**

This error relates to a new update to cdk so run `npm install -g aws-cdk` again to update your cdk to the latest version and then run the deployment step again for each account that your stacks are deployed.

* **`cdk synth`** **not running**

One of the following would solve the problem:

    * Docker is having an issue so restart your docker daemon
    * Refresh your awscli credentials
    * Clear all cached cdk outputs by running `make clean`
