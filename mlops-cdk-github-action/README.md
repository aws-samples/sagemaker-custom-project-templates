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
│   ├── cdk-account-setup.sh
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

1. Create AWS GitHub OpenId connect IAM role, follow the below process : https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services

2. Create following GitHub secrets : AWS_ACCOUNT_OPENID_IAM_ROLE, AWS_REGION, AWS_ACCOUNT

3. GitHub Action deployment workflow CI/CD pipeline (.github/workflows/sm_template_register_service_catalog.yml) will now handle all deployments.




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