# MLOps SageMaker Project Template for GitHub Actions
This repository contains the resources that are required to deploy the MLOps SageMaker Project Template with GitHub Action as the CI/CD.

- [MLOps SageMaker Project Template](#mlops-sagemaker-project-template)
  - [Solution Architecture](#solution-architecture)
  - [Repository Structure](#repository-structure)
  - [Deployment Options](#deployment-options)
    - [CI/CD Deployment of Service Catalog Stack](#cicd-deployment-of-service-catalog-stack)
    - [Manual Deployment of Service Catalog Stack](#manual-deployment-of-service-catalog-stack)
  - [Clean-up](#clean-up)
  - [Troubleshooting](#troubleshooting)

## Solution Architecture

![mlops project architecture](diagrams/github_action_mlops_architecture.jpg)


## Repository Structure

```
.
├── LICENSE.txt
├── Makefile
├── README.md
├── app.py
├── cdk.json
├── diagrams
├── .github                                   <--- contains the GitHub Action WorkFlow script
│   ├── sm_template_register_service_catalog.yml  
├── mlops_sm_project_template
│   ├── README.md
│   ├── __init__.py
│   ├── cdk_helper_scripts
│   ├── config
│   │   └── constants.py                      <--- global configs to be used in CDK stacks
│   ├── core_stage.py                     <--- entry to build the differnt stacks
│   ├── service_catalog_stack.py              <--- stack for service catalog setup and template deployment
│   └── templates
│       ├── basic_project_stack.py                <--- stack for basic sagemaker project template setup - DEV Accounts provided in constants.py
│       └── pipeline_constructs
│           ├── build_pipeline_construct.py       <--- construct containing CI/CD pipeline linked to the build app
│           └── deploy_pipeline_construct.py      <--- construct containing CI/CD pipeline linked to the deploy app
├── requirements-dev.txt
├── requirements.txt                          <--- cdk packages used in the stacks (must be installed)
├── scripts                                   <--- shell scripts to automate part of the deployments
│   └── install-prerequisites-brew.sh
└── seed_code                                 <--- code samples to be used to setup the build and deploy repositories of the sagemaker project
    ├── build_app
    └── deploy_app
```

## Deployment Options

There are two deployment options for the SageMaker Project Template to the Service Catalog in the target account:

- **[CI/CD Deployment of Service Catalog Stack](#cicd-deployment-of-service-catalog-stack)** - deploy by using GitHub Action CICD pipeline by cloning the repository to your GitHub Repository

- **[Manual Deployment of Service Catalog Stack](#manual-deployment-of-service-catalog-stack)** - deploy directly to the targeted accounts using CDK commands from your local development setup



### CI/CD Deployment of Service Catalog Stack
Register the SageMaker Project Template through GitHub Action Pipeline CI/CD ( Preferred )

Follow below steps:

1. Create a GitHub repository with the content of this folder.
   1. Fork the repo.
   2. Clone the repo to your local machine.
   3. `cd` into the repo folder and then into the `mlops-cdk-github-action` folder.
   4. `git init` in the `mlops-cdk-github-action` folder.
   5. Before you push the repo to your GitHub account, make sure the Personal Access Token you're using has not only the `repo` scope, but also the `workflow` scope. This is required for the GitHub Action to be able to trigger the workflow.
   1. Fork the repo.
   2. Clone the repo to your local machine.
   3. `cd` into the repo folder and then into the `mlops-cdk-github-action` folder.
   4. `git init` in the `mlops-cdk-github-action` folder.
   5. Before you push the repo to your GitHub account, make sure the Personal Access Token you're using has not only the `repo` scope, but also the `workflow` scope. This is required for the GitHub Action to be able to trigger the workflow.
2. Make sure you have the SageMaker domain ready with a user profile, if you don’t have a SageMaker Domain created yet. Follow the steps to create it: [Create SageMaker Domain](https://docs.aws.amazon.com/sagemaker/latest/dg/onboard-quick-start.html)
3. Once you have the domain created. Navigate to Domain, Click on your Domain, Click on User Profile, on the right-hand side pane copy the “Execution Role”.
![screenshot1](diagrams/domain_execution_role.png)
4. Ensure that the above identified Execution role has the following SageMaker project IAM permissions:
    ```commandline
    {
    "Version": "2012-10-17",
    "Statement": [
        {
        "Sid": "VisualEditor0",
        "Effect": "Allow",
        "Action": [
            "sagemaker:DescribeProject",
            "sagemaker:CreateProject",
            "sagemaker:DeleteProject",
            "sagemaker:ListProjects",
            "sagemaker:UpdateProject "
        ],
            "Resource": "*"
        }
       ]
    }
    ```
5. Go to AWS Systems Manager, then go to the Parameter Store, and create a String Parameter of Data Type text named “/sagemaker/execution/role” and provide the value as the SageMaker Execution Role ARN.

![screenshot2](diagrams/sagemaker_parameter.png)

6. Create an IAM OpenID Connect (OIDC) identity provider. Follow the steps outlined in [AWS Documentation](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html#manage-oidc-provider-console) to create an IAM OIDC identity provider. In the Provider URL field enter `https://token.actions.githubusercontent.com`, and click Get Thumbprint. In the Audience filed, enter `sts.amazonaws.com`

![screenshot3](diagrams/github_identity_provider.png)

7. Create an IAM role using OIDC identify provider. OIDC allows your GitHub Actions workflows to access resources in Amazon Web Services (AWS), without needing to store the AWS credentials as long-lived GitHub secrets. [follow more](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services) 

![screenshot4](diagrams/github_iam_role_create.png)

Assign below permissions to this role (_Note: For setup we are providing broad permission to those services, later you need to trim down the permissions to only required one_)
```
    AmazonEC2ContainerRegistryFullAccess
    AmazonS3FullAccess
    AWSServiceCatalogAdminFullAccess
    AWSCloudFormationFullAccess
    IAMFullAccessAmazon
    SageMakerFullAccess
```
Create the role and post creation, open the newly created role and update the Trust Relationship to this(update aws account and GitHub repo details)
    
```
{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Federated": "arn:aws:iam::<your_aws_account_id>:oidc-provider/token.actions.githubusercontent.com"
                },
                "Action": "sts:AssumeRoleWithWebIdentity",
                "Condition": {
                    "StringEquals": {
                        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                    },
                    "StringLike": {
                        "token.actions.githubusercontent.com:sub": "repo:<github_user_name_casesensetive>/<newly_created_github_repo_name>:*"
                    }
                }
            }
        ]
    }
```
   
8. Create GitHub secrets: If you haven't yet cloned the repository mentioned in this blog, now is the time to do so. GitHub Secrets are encrypted variables that can be created within your GitHub organization or repository. These secrets can then be utilized in your GitHub Actions workflows. In order to run your GitHub Actions pipelines successfully, you must create the following three required secrets in your cloned repository.
       ```
       AWS_ACCOUNT_OPENID_IAM_ROLE - The ARN of the IAM role created in the previous step.
       AWS_REGION - The AWS region where you will be deploying the SageMaker Project Template.
       AWS_ACCOUNT - The AWS account where you will be deploying the SageMaker Project Template
      ```
   
9. In the cloned repository, you will see the "Sagemaker Project Template Registration in Service Catalog" workflow in your GitHub Actions. Run this workflow to deploy the SageMaker organizational template to AWS Service Catalog.

![screenshot5](diagrams/github_action_trigger.png)

10. When the above GitHub workflow completes successfully, you will be able to view the custom SageMaker Project template from your SageMaker Studio, as depicted in the following screenshot.

![screenshot6](diagrams/sagemaker_custom_project.png)

11. Follow the project creation, and on the project creation details page provide project name (lower case only), your GitHub username (case-sensitive) and GitHub [personal access token](https://docs.github.com/en/enterprise-server@3.4/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token). 
_Make sure while creating personal access token has minimum those permissions:_   **repo, workflow, delete_repo**

![screenshot7](diagrams/project_create_page.png)


### Manual Deployment of Service Catalog Stack
Register the SageMaker Project Template from local development.

#### Pre-requisites

* If you have a mac machine with [Homebrew](https://brew.sh/) installed, you can use `scripts/install-prerequisites-brew.sh` to install the prerequisites and setup the python environment

1. This is an AWS CDK project written in Python 3.8. Here's what you need to have on your workstation before you can deploy this project. It is preferred to use a linux OS to be able to run all cli commands and avoid path issues.

   * [Node.js](https://nodejs.org/)
   * [Python3.8](https://www.python.org/downloads/release/python-380/) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
   * [AWS CDK v2](https://aws.amazon.com/cdk/)
   * [AWS CLI](https://aws.amazon.com/cli/)
   * [Docker](https://docs.docker.com/desktop/)



2. It is necessary to create a simple way to interact with multiple AWS credentials. We recommend the creation of an AWS profile per account with enough permission to deploy to CloudFormation following the instructions [here](https://docs.aws.amazon.com/toolkit-for-visual-studio/latest/user-guide/keys-profiles-credentials.html#adding-a-profile-to-the-aws-credentials-profile-file) . For example, the `.aws/credentials` should look like:

    ```
    [mlops-dev]
    aws_access_key_id = YOUR_ACCESS_KEY_ID
    aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
    aws_session_token = YOUR_SESSION_TOKEN  # this token is generated if you are using an IAM Role to assume into the account
    ```
3. Make sure you have the SageMaker domain ready with a user profile, if you don’t have a SageMaker Domain created yet. Follow the steps to create it: [Create SageMaker Domain](https://docs.aws.amazon.com/sagemaker/latest/dg/onboard-quick-start.html)
4. Once you have the domain created. Navigate to Domain, Click on your Domain, Click on User Profile, on the right-hand side pane copy the “Execution Role”.

![screenshot1](diagrams/domain_execution_role.png)

4. Ensure that the above identified Execution role has the following SageMaker project IAM permissions:
    ```
    {
    "Version": "2012-10-17",
    "Statement": [
        {
        "Sid": "VisualEditor0",
        "Effect": "Allow",
        "Action": [
            "sagemaker:DescribeProject",
            "sagemaker:CreateProject",
            "sagemaker:DeleteProject",
            "sagemaker:ListProjects",
            "sagemaker:UpdateProject "
        ],
            "Resource": "*"
        }
       ]
    }
    ```
5. Go to AWS Systems Manager, then go to the Parameter Store, and create a String Parameter of Data Type text named “/sagemaker/execution/role/” and provide the value as the SageMaker Execution Role ARN.

![screenshot2](diagrams/sagemaker_parameter.png)


#### Project Build and Deploy

Follow the steps below to achieve that:

1. Clone this repository in your work environment (e.g. your laptop)

2. Change directory to project root : `mlops-cdk-github-action`

    ```
    cd mlops-cdk-github-action
    ```
3. Make sure all the Pre-requisites section is installed(Node, Docker, Python). 
4. Install dependencies in a separate python virtual environment using your favourite python packages manager. You can refer to `scripts/install-prerequisites-brew.sh` for commands to setup a python environment.

    ```
     pip install -r requirements.txt
    ```
5. Navigate to `.env` file on project root level. Add your AWS Account and Region.
  _[don't commit this file, as this is only for local development]_
    ```
    AWS_ACCOUNT=<your_aws_account_id_on_which_you_want_to_register>
    AWS_REGION=<aws_region>         
    ```
6. Ensure your docker daemon is running

7. Bootstrap the account manually, then run the following command from project root folder:

    ```
    cdk bootstrap aws://<target account id>/<target region> --profile <your_aws_profile_for_the_target_account>
    ```

    The following is an example of the same:
    ```
    cdk bootstrap aws://1234567890/us-east-1
    ```

    for more information read the [AWS CDK documentation on Bootstrapping](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html#bootstrapping-howto)

8. Build the CDK stack
  
    ```
    cdk synth
    ```

9. Deploy the stage to AWS Account

    ```
    cdk --app ./cdk.out/assembly-dev deploy —all --profile <your_aws_profile_for_the_target_account>
    ```

  as a stage could include a combination of stacks `--all` flag is included with the `deploy` command


## Clean-up

In case you used the local deployment, once you are done with testing the new feature that was deployed locally, run the following commands to clean-up the environment:
```
# destroy stage to target account (make it match your stack name)
cdk --app ./cdk.out/assembly-dev destroy —all --profile <your_aws_profile_for_the_target_account>
```
## Troubleshooting