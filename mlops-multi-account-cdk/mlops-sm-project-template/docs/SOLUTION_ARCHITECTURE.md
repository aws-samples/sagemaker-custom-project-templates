# Solution Architecture

![mlops project architecture](../diagrams/MLOPs%20Foundation%20Architecture-mlops%20project%20cicd%20architecture.jpg)

- [Solution Architecture](#solution-architecture)
  - [Service Catalog Stack](#service-catalog-stack)
  - [CodeCommit Stack](#codecommit-stack)
  - [Pipeline Stack](#pipeline-stack)

## Service Catalog Stack

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
- **2 assets**, a zip for the **seed code** for each of the **build app** and the **deploy app**, stored in CDK Assets bucket, this bucket is created as part of **CDKToolkit stack**. A SSM Parameter is created for each asset's s3 key and also for the s3 bucket name. These parameters are used in [SageMaker Project Stack](#sagemaker-project-stack). The assets structure is documented in [MLOps Foundation blog](https://aws.amazon.com/blogs/machine-learning/mlops-foundation-roadmap-for-enterprises-with-amazon-sagemaker/) and can be found in `seed_code` folder for reference.
- **SSM Parameters** containig configuration about the target deployment accounts: **DEV**, **PREPROD** and **PROD** i.e. account id, region. These Parameters are used by the deploy app.

Once this stack is deployed in the account, the template will be usable by Amazon SageMaker Studio Domain user with the role: **Execution Role** that was provided to this stack.

This stack deploys the following templates:
- [Basic Project Template](templates/BASIC_PROJECT_TEMPLATE.md)
- [Dynamic Account Project Template](templates/DYNAMIC_ACCOUNT_PROJECT_TEMPLATE.md)
- [BYOC Project Template](templates/BYOC_PROJECT_TEMPLATE.md)

## CodeCommit Stack
*This stack is only needed if you want to handle deployments of this folder of the repository to be managed through a CICD pipeline.*

This stack handles setting up an AWS CodeCommit repository for this folder of the repository. This repository will be used as the source for the CI/CD pipeline defined in [Pipeline Stack](#pipeline-stack). The repository will be named based on the value defined in `mlops_sm_project_template/config/constants.py` with this variable `CODE_COMMIT_REPO_NAME`. The repository will be intialised with a default branch as defined in the `constants.py` file under `PIPELINE_BRANCH` variable.


## Pipeline Stack

*This stack is only needed if you want to handle deployments of this folder of repository to be managed through a CICD pipeline. The pipeline is configured to deploy to 1 account: DEV and will deploy the service catalog stack to the target account*

The CICD pipeline in this repository is setup to monitor an AWS CodeCommit repository as defined in [CodeCommit Stack](#codecommit-stack).

If you are using other sources like github or bitbucket for your repository, you will need to modify the connection to the appropriate repository as defined in `mlops_sm_project_template/pipeline_stack.py`. This can be done using AWS CodeStar but must be setup on the account.

Make sure the pipelines also point to your targeted branch; by default the pipeline is linked to `main` branch events, this is defined in the `constants.py` file under `PIPELINE_BRANCH` variable.

`constants.py` also contains information about the target accounts you want to use for this repository CI/CD pipeline and the target deployment accounts: **DEV**, **PREPROD** and **PROD**, this information will also be deployed in SSM Parameter in the DEV account for the Deploy App CI/CD pipeline.

The pipeline will deploy all stacks and resources to the appropriate accounts.
