# Base Infrasturcure 

This repository defines the infrastructure to setup your MLOps platform. 

```
.
├── Makefile
├── README.md
├── config.json
├──.github
    ├── workflows
    |   ├── deploy.yml
    |   ├── destroy.yml
    |   └── quality-check.yml
└── terraform
    ├── account_config
    │   ├── dev
    │   │   └── terraform.tfvars
    │   ├── preprod
    │   └── prod
    ├── modules
    │   ├── kms
    │   └── **
    ├── dev
    │   ├── README.md
    │   ├── *.tf
    │   ├── lambdas
    │   │   ├── functions
    │   │   │   ├── clone_repo_lambda
    │   │   │   │   ├── **.py
    │   │   │   └── trigger_workflow_lambda
    │   │   └── layers
    │   │       └── python_github_layer.zip
    │   ├── sagemaker_templates
    │   │   ├── sagemaker_project_train.yaml
    │   │   ├── sagemaker_project_train_and_deploy.yaml
    │   │   └── sagemaker_project_workflow.yaml
    ├── preprod
    │   ├── README.md
    │   ├── *.tf
    └── prod
        ├── README.md
        └── *.tf
```

## Prerequisites

- Ensure your target AWS account have been bootstrapped first.

- Ensure you have a GitHub PAT.

- Ensure the contents of this folder has been move to a stand-alone git repository.

- Ensure the following Github template repos are avaialble in your Github organization:
  1. sagemaker-mlops-terraform-byoc-template
  2. sagemaker-mlops-terraform-deploy-rt-template
  3. sagemaker-mlops-terraform-workflow
  4. sagemaker-mlops-terraform-deploy-batch-template 
  5. sagemaker-mlops-terraform-training-template

## Get Started

Get started by setting up your first dev, preprod, and prod environments on AWS accounts. 

### 1. What gets deployed:

The base infrastructure will deploy:
- A secure Data Science exploration environment for your data scientists to explore and train their models inside a SageMaker studio environment.
- Networking. Either run SageMaker studio in a VPC, or be able to create SageMaker Endpoints and other infrastructure inside VPCs.
  - Default networking is a kick start example and the repository is designed to be able to import existing VPCs created by your organization.
- SageMaker Studio users (Lead Data Scientist and Data Scientist) and associated roles and policies.
- Service catalog portfolio and products for custom SageMaker projects.
- Lambda functions that facilitate the API calls to your Github organization. Your GitHub PAT is stored in AWS Secret Manager.

### 2. GitHub Secrets

1. AWS Role Name

In previous steps, you bootsrapped your AWS accounts, depoying an AWS IAM role that can be assumed by GitHub actions. If you did not customize the role name, this should be `aws-github-oidc-role`.

Create a new [Secret in this GitHub repository](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions) under the name `AWS_ASSUME_ROLE_NAME` and set its value to the role name.

> **_NOTE:_**: this is not the ARN, just the role ID.

2. GitHub PAT

To automatically create clones of template repos when a sagemaker project is deployed, we need to save and maintain GitHub credentials safely on AWS. This is done for you in this repository using AWS Secrets manager. 

Create another secret under the name `PAT_GITHUB`.

### 3. Configure your target accounts

**Make these changes and push to the main branch for the Continuous integration process to kick in.**

1. `config.json`

The Base Infrastructure is deployed by configuring [config.json](config.json). In this file, you can specify multiple JSON Objects, that correspond to units in your business. Each object requires a:

- "region"
- "dev_account_number"
- "preprod_account_number"
- "prod_account_number"

Open `config.json` and edit the content with your account details:

```json
{
  "my_business_unit": {
    "region": "TODO",
    "dev_account_number": "TODO",
    "preprod_account_number": "TODO",
    "prod_account_number": "TODO"
  }
}
```
2. `.github/workflows/deploy.yml`, `.github/workflows/destroy.yml`, and `.github/workflows/quality-checks.yml`

Then, update the workflows with a list of your business units:

```
strategy:
      matrix:
        business_unit: ["my_business_unit"] 
```

> **_NOTE:_**: This needs to be done 3 times in each of the files, one for each job (TF Apply to Dev, TF Apply to PreProd, TF Apply to Prod).

3. (Optional) Overwrites

The [config.json](config.json) file can also be used in order to overwrite tfvars variables during run time. 

You can also at this point change any tfvars locally in [account_config](terraform/account_config) 

**If you have succesfully made these changes and pushed your code to the main branch, the `Deploy infrastructure` Github action should start running. Make sure the action is succesful and infrastructure is deployed. More details about the CICD workflow on this repository in covered in the next section.**

## CICD Workflows

There are three [GitHub Actions Workflows](https://docs.github.com/en/actions/quickstart) associated to this repository.

1. "Deploy infrastructure" in `deploy.yml`

This action is trigerred when a commit is made to the `main` branch (for example when a pull request is merged). It deploys base infrastructure to all dev, preprod, and prod accounts across business units in parallel.

2. "Destroy infrastructure" in `destroy.yml`

This action is only trigerred manually on [workflow_dispatch](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows). It destroys all base-infrastructure for target business units. Note Machine Learning code deployed via SageMaker project is _durable_ and will continue to live even after you destroy base-infrastructure. 

3. "Quality Checks" in `quality-checks.yml``

This action is trigerred each time a pull request is created to merge changes into the `main` branch. All checks on the pull request should pass before merging changes.

The checks include static checking using [checkov](https://github.com/bridgecrewio/checkov) and a `terraform plan` step against the target accounts.

## Importing Networking
We create the necessary networking components in our Base Infrastructure, however you may have your own existing networking that you would like to deploy. Here is how you do it: 
1. Comment out the networking module from all necessary environments in the main.tf, e.g. for dev: [main.tf](terraform/dev/main.tf)
2. In modules, create a new folder e.g. "imported_networking". Here you can import your resources using the "data" source. For the application to work, make sure the list of outputs is the same (found in [outputs.tf](terraform/modules/networking/outputs.tf)) & make sure the list of ssm parameters is the same (found in [ssm.tf](terraform/modules/networking/ssm.tf))
3. In the main.tf of each relevant environment, create a new module definition, calling your newly created module, like so:
```
module "networking" {
  source = "../modules/imported_networking" // your module folder name
  // any vars you need to import
} 
```
## Deploy you first project

You are now ready to launch SageMaker Studio environment and launch your first SageMaker project! 
