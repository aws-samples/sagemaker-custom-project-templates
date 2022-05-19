# MLOps Foundation Infrastructure

This repository contains the resources that are required to deploy the MLOps Foundation infrastructure. It contains the definition of a secure networking with Amazon VPC, Subnets, Security Group and Amazon VPC Endpoints to be used with Amazon SageMaker Studio. It also defines the setup for Amazon SageMaker Studio Domain and creates SageMaker Studio User Profiles for Data Scientists and Lead Data Scientists.

## Solution Architecture

![mlops foundation infrastruction](diagrams/MLOPs%20Foundation%20Architecture-mlops%20infrastructure%20architecture.jpg)
### Networking Stack

*This is an optional stack for the scenario that the account does not have an existing VPC configured. Switch to* *`release/no-vpc`* *for this repository setup with an existing VPC. You must ensure that the existing VPC contains most of the components that are created in this stack.*
![networking stack](diagrams/MLOPs%20Foundation%20Architecture-mlops%20secure%20networking.jpg)

The networking stack deploys all required resources to create a secure environment to run machine learning workloads in AWS. The following resources are deployed:

1. VPC with 3 Availability Zones (AZs), 1 public subnet and 1 private subnet (attached with a NAT Gateway) in each AZ, DNS hostnames and support enabled, and 1 NAT Gateway
2. VPC Endpoints deployed in each deployment account (DEV/PREPROD/PROD) as shown in the diagram.

|S3	|SageMaker API	|SageMaker Runtime	|SageMaker Notebook	|CodeCommit	|CodeCommit Git	|
|---	|---	|---	|---	|---	|---	|
|SSM	|CloudWatch Monitoring	|CloudWatch Logs	|ECR Docker	|ECR API	|KMS	|
|STS	|CodeArtifact API	|CodeArtifact Repositories	|	|	|	|

3. SSM parameters are used to store information about the VPC and its related components in each deployment account (DEV/PREPROD/PROD)

### SageMaker Studio Stack

*This stack is only deployed in the DEV account*
![sagemaker studio stack](diagrams/MLOPs%20Foundation%20Architecture-sagemaker%20studio%20stack.jpg)

This stack handles the deployment of the following resources:

1. SageMaker Studio Domain requires, along with
2. IAM roles which would be linked to SM Studio user profiles. User Profile creating process is managed by the config files in `mlops_infra/config/dev/data_scientists.yml` and `mlops_infra/config/dev/lead_data_scientists.yml`. you can simply add new entries in the list to create a new user. The user will be linked to a role depending on which yml you add him to and will have a prefix defined in the yml files.

```
  users:
    - user_profile_name: "X"
```

3. Default SageMaker Project Templates are also enabled on the account on the targeted region using a custom resource; the custom resource uses a lambda function, `functions/sm_studio/enable_sm_projects`, to make necessary SDK calls to both Amazon Service Catalog and Amazon SageMaker.

### Pipeline Stack

*This stack is only needed if you want to handle deployments of this repository to be managed through a CICD pipeline. The pipeline is configured to deploy to 3 accounts, DEV, PREPROD and PROD*

The CICD pipelines in this repository are setup to monitor an AWS CodeCommit repository and must be setup beforehand; the name of the repository is defined in `mlops_infra/config/constants.py` so change the value of this variable `CODE_COMMIT_REPO_NAME`.

If you are using other sources like github or bitbucket for your repository, you will need to modify the connection to the appropriate repository as defined in `mlops_offering/pipeline_stack.py`. This can be done using AWS CodeStar but must be setup on the account.

Make sure the pipelines also point to your targeted branch; by default the pipeline is linked to `main` branch events, this is defined in the `constants.py` file under `PIPELINE_BRANCH` variable.

`constants.py` also contains information about the target accounts you want to use for this repository CICD pipeline and the target deployment accounts (DEV/PREPROD/PROD).

The pipeline will deploy all stacks and resources to the appropriate accounts.


## Solution Deployment

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
├── cdk.context.json
├── cdk.json
├── diagrams
├── functions                                   <--- lambda functions and layers
│   └── sm_studio                               <--- sagemaker studio stack related lambda function
│       └── enable_sm_projects                  <--- lambda function to enable sagemaker projects on the account and links the IAM roles of the domain users (used as a custom resource)
├── mlops_infra
│   ├── config
│   │   ├── config_mux.py
│   │   ├── constants.py                        <--- global configs to be used in CDK stacks regardless of the account
│   │   └── dev                                 <--- configs for the dev account (default configs if not present in other config folders)
│   │       ├── data_scientists.yml             <--- yml file containing a list of users to be linked to data scientist role
│   │       └── lead_data_scientists.yml        <--- yml file containing a list of users to be linked to lead data scientist role
│   ├── constructs
│   │   └── sm_roles.py                         <--- construct containing IAM roles for sagemaker studio users
│   ├── networking_stack.py                     <--- stack to setup a VPC and all related components i.e. subents and vpc endpoints as required
│   ├── pipeline_stack.py                       <--- stack for CICD with code pipeline setup for the repo
│   └── sagemaker_studio_stack.py               <--- stack to create sagemaker studio domain along with related IAM roles and the domain users
├── requirements-dev.txt
├── requirements.txt                            <--- cdk packages used in the stacks (must be installed)
└── scripts                                     <--- shell scripts to automate part of the deployments
    ├── cdk-account-setup.sh
    └── install-prerequisites-brew.sh
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
aws_session_token = YOUR_SESSION_TOKEN

[mlops-dev]
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
aws_session_token = YOUR_SESSION_TOKEN

[mlops-preprod]
...

[mlops-prod]
...
```

(Optionally) Alternatevely, If you use isengardcli to manage access to your aws accounts, you can add aws profiles to your `.aws/config` by running the following command `isengardcli add-profile`. You can then supply the name of the profile to run the setup script in Solution Deployment section. Expect the following to be added to `.aws/config`:

```
[profile <email>-<role>]
    output = json
    region = us-west-2
    credential_process = isengardcli credentials --awscli <email>@amazon.com —role <role>
```

### Deployment Options

***Warning:** It is best you setup a python environment to handle all installs for this project and manage python packages. Use your preferred terminal and editor to run the following commands.*

There are two deployment options for the infrastructure to the accounts:

1. **[CI/CD Deployment](#1-cicd-deployment)** - deploy by using a governance account setup and a CICD pipeline linked to this repository

2. **[Manual Deployment](#2-manual-deployment)** - deploy without a governance account setup and directly to the targeted accounts (1 or more) using CDK commands


For both options, the first step is to bootstrap the AWS accounts.

### Bootstrap AWS Accounts

1. Clone this repository in your work environment (e.g. your laptop), make sure to run `mwinit` as this is an internal gitlab instance that uses your own yubikey credentials to authenticate

```
git clone git@ssh.gitlab.aws.dev:mlops-foundation/mlops-infra.git
```

2. Change directory to `mlops-infra` root

```
cd mlops-infra
```

3. Install dependencies in a separate python environment using your favourite python packages manager. You can refer to `scripts/install-prerequisites-brew.sh` for commands to setup a python environment.

```
 pip install -r requirements.txt
```

4. Run `make init` to setup githooks

5. (Option 1) Bootstrap your deployment target accounts (e.g. governance, dev, etc.) using our script in `scripts/cdk-account-setup.sh.` Ensure that you have the account ids ready and the corresponding AWS profiles with credentials created in your `~/.aws/credentials` for each account (see above).

The script will request the 4 accounts, i.e. governance, dev, preprod and prod, and the corresponding AWS profiles as inputs. If you want to only deploy to 1 account you can use the same id for all account variables or pass the same values in the script.

<add screenshot here of sccript execution>

5. (Option 2) If you want to bootstrap the account manually, then run the following command for each account:

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


### 1. CI/CD Deployment

1. Deploy the deployment CI/CD pipeline in your governance account (one time operation). This is the CI/CD pipeline that would deploy your required infrastructure to setup your networking in the accounts and SageMaker Studio Domain in the Dev Account:

```
# builds the pipeline stack and install all assets
cdk synth
# deploy stack to target account, use the governance account profile for this
cdk deploy
```

2. the deployment CI/CD pipeline will now handle all deployments for the other stacks based on the updates to the main branch

### 2. Manual Deployment

It is possible to deploy a specific stage (in `pipeline_stack.py`  refer to classes inheriting `Stage` class from `aws_cdk`). The same is possible to a singular stack (follow the same deployment steps as the pipeline stack).


1. Add a custom id to the target stage in `app.py`

```
# Personal Stacks for testing locally, comment out when committing to repository
CoreStage(
    app,
    "Personal",  ## change this to another stage name when doing local tests
    deploy_sm_domain=True, ## change this to False if you only want to deploy the VPC stack
    env=deployment_env,
)
```

2. Deploy the stage

```
cdk --app ./cdk.out/assembly-Personal deploy —all
# builds the pipeline stack and install all assets
cdk synth
# deploy stage to target account (make it match your stack name)
```

as a stage could include a combination of stacks `--all` flag is included with the `deploy` command

once you are done with testing the new feature that was deployed locally, run the following to clean-up the environment:

```
cdk --app ./cdk.out/assembly-Personal destroy —all
# destroy stage to target account (make it match your stack name)
```

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
* **[Error at /ml-deploy-pipeline/****<****env****>****/networking] Need to perform AWS calls for account X, but no credentials have been configured**

You can resolve this error by adding availability zone information to `cdk.context.json`. This error happens as CDK tries to do a lookup on the account to check which Availability Zones does the region of the target account have available and if it can be deployed across the targeted 3 AZs.