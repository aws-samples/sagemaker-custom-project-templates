# Advanced topics
The topics defined here assume you have already deployed the solution once following the steps in the main [README](README.md)

- [Advanced topics](#advanced-topics)
  - [Create new template](#create-new-template)
  - [Setup CodeCommit with this repository](#setup-codecommit-with-this-repository)
  - [Test the created sagemaker templates](#test-the-created-sagemaker-templates)
  - [Delete a Project](#delete-a-project)
  - [Delete a Domain](#delete-a-domain)

## Create new template
You can use `templates/basic_project_stack.py` as the bases to create your own template. You need to follow these steps to create your own template:
1. create a new file in `mlops_sm_project_template/templates` with the suffix `_stack.py` (this is very important as the code will look for files with that suffix when it comes to pushing the templates)
2. copy the following into the new created stack:
```
from aws_cdk import (
    Stack,
    Tags,
)


from constructs import Construct

class MLOpsStack(Stack):
    DESCRIPTION: str = "<add a description of the template here>"
    TEMPLATE_NAME: str = "<add a unique name here as this will appear in sagemaker studio console>"

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define required parmeters
        project_name = aws_cdk.CfnParameter(
            self,
            "SageMakerProjectName",
            type="String",
            description="The name of the SageMaker project.",
            min_length=1,
            max_length=32,
        ).value_as_string

        project_id = aws_cdk.CfnParameter(
            self,
            "SageMakerProjectId",
            type="String",
            min_length=1,
            max_length=16,
            description="Service generated Id of the project.",
        ).value_as_string

        Tags.of(self).add("sagemaker:project-id", project_id)
        Tags.of(self).add("sagemaker:project-name", project_name)
```
The 2 parameters defined here are mandatory for any template created for Sagemaker Projects.

3. now add any resources that you would like to create as part of your template i.e. S3 bucket, a pipeline to deploy/build the model .. etc. 


## Setup CodeCommit with this repository
You would wonder after you have cloned this repository and deployed the solution how would you then start to interact with your deployed CodeCommit repository and start using it as a main repository and push changes to it. You have 2 options for this:
1. Clone the created CodeCommit repository and start treating it seperately from this repository
2. Just use this folder as a repository

For the second option, you can do the following (while you are in the folder `mlops-sm-project-template`):
```
git init
```
this will create a local git for this folder which would be separate from the main so you can treat it as any git repo and it would not impact the main repository git. So, add the CodeCommit Repository as a remote source:
```
git remote add origin https://git-codecommit.eu-west-1.amazonaws.com/v1/repos/mlops-sm-project-template
```
Ensure you have configured your machine to connect to CodeCommit and make `git push` or `git pull` commands to it; follow [Step 3 from the AWS documentation](https://docs.aws.amazon.com/codecommit/latest/userguide/setting-up-https-unixes.html).

Now you can interact with the CodeCommit repository as normal. You will need to do the following for the first commit:
```
git add -A
git commit -m "first commit"
export AWS_PROFILE=mlops-governance
git push origin main
make init   # this will enable precommit which will now block any further pushes to the main branch
```

Ensure that your git uses the branch name **main** by default, otherwise the push command might fail and you will need to create a main branch then push changes through it.

If you want to push the changes you made back to the main repository this folder belongs to you can just run this command:
```
rm -fr .git
```
This will remove the git settings from this folder so it would go back to the main repository settings. You can then raise a PR to include your changes to the main repository in GitHub.


## Test the created sagemaker templates
***NOTE:** make sure to run `cdk synth` before running any of the commands defined below.*

You will need to deploy the `service catalog stack` as that would setup your account with the required resources and ssm parameters before you can start testing your templates directly. If you don't have the service catalog stack already deployed in your account, you can achieve this by running the following command:
```
cdk --app ./cdk.out/assembly-Personal deploy —all --profile mlops-dev
```

otherwise make sure you have these ssm parameters defined:
- in the dev account:
  - /mlops/dev/account_id
  - /mlops/code/seed_bucket
  - /mlops/code/build
  - /mlops/code/build/byoc
  - /mlops/code/deploy
- in the preprod account:
  - /mlops/preprod/account_id
  - /mlops/preprod/region
- in the prod account:
  - /mlops/prod/account_id
  - /mlops/prod/region

**OPTION 1** For quick testing of the sagemaker templates, you could deploy the json generated by CDK directly in your account by running the following command:
```
aws cloudformation deploy \
	--template-file ./cdk.out/byoc-project-stack-dev.template.json \
	--stack-name byoc-project-stack-dev \
	--region eu-west-1 \
	--capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
	--disable-rollback \
  --s3-bucket <any s3 bucket in the account, preferred cdk bootstrap bucket> \
  --profile mlops-dev \
	--parameter-overrides \
	  SageMakerProjectName=mlops-test-0 \
	  SageMakerProjectId=sm12340
```
This command will deploy the byoc project stack if you want to deploy other templates just change the `--template-file`, if you want to create a new stack you can change the other fields as well. 

**OPTION 2** It is also possible to use CDK command for this exact purpose but this would require you to add the following to `app.py` file:
```
from mlops_sm_project_template.templates.byoc_project_stack import MLOpsStack

MLOpsStack(
    app,
    "test",
     env=deployment_env,
)
```
The run `cdk synth` and then run the following to deploy:
```
cdk deploy test --parameters SageMakerProjectName=mlops-test \
    --parameters SageMakerProjectId=sm1234 --profile mlops-dev
```

## Delete a Project
Deleting a project is a very involved process especially if you want to perform a complete delete of all the resources that were deployed for this project and even more tricky if those resource were deployed in other accounts.  

## Delete a Domain
Deleting a domain through CloudFormation will always fail especially if you have users with running applications in it. To be able to delete a domain you would need to run the following using `boto3` (you will need to know the `domain_id`):
```
domain_apps = sm_client.list_apps(DomainIdEquals=domain_id)

    for app in domain_apps["Apps"]:
        response = sm_client.delete_app(
            DomainId=app["DomainId"],
            UserProfileName=app["UserProfileName"],
            AppType=app["AppType"],
            AppName=app["AppName"],
        )
        logger.info(response)

    logger.info(f"finished deleting apps for {domain_id} SageMaker Domain")

    domain_users = sm_client.list_user_profiles(DomainIdEquals=domain_id)

    for user_profile in domain_users["UserProfiles"]:
        response = sm_client.delete_user_profile(
            DomainId=user_profile["DomainId"],
            UserProfileName=user_profile["UserProfileName"],
        )
        logger.info(response)

    logger.info(f"finished deleting user profiles for {domain_id} SageMaker Domain")
```