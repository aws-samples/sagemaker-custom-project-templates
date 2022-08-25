# MLOps Foundation SageMaker Project Template
This repository contains the resources that are required to deploy the MLOps Foundation SageMaker Project Template.

- [MLOps Foundation SageMaker Project Template](#mlops-foundation-sagemaker-project-template)
  - [Solution Architecture](#solution-architecture)
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

For a detailed explaination of the solution architecture go to [docs/SOLUTION_ARCITECTURE.md](docs/SOLUTION_ARCHITECTURE.md)

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
