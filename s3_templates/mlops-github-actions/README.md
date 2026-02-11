# ModelOps using Amazon SageMaker and GitHub Actions (S3-Based Template)

This is an S3-based SageMaker project template that implements ModelOps using Amazon SageMaker and GitHub Actions. This template has been migrated from the original Service Catalog-based approach to the new recommended S3-based deployment method.

## Overview

This template automates a model-build pipeline that includes steps for:
- Data preparation
- Model training  
- Model evaluation
- Registration in the SageMaker Model Registry
- Automated deployment to staging and production environments upon approval

## Architecture

The template creates the following AWS resources:
- **S3 Bucket**: For storing ML artifacts
- **Lambda Function**: Triggers GitHub workflows when models are approved
- **EventBridge Rule**: Monitors SageMaker Model Registry for approved models
- **SageMaker Code Repository**: Links to your GitHub repository
- **IAM Roles**: Proper permissions for Lambda execution

## Prerequisites

Set these environment variables to make the following commands reusable and easier to run.

```bash
export AWS_REGION=<your AWS Region>
export AWS_ACCOUNT_ID=<your AWS Account ID>
export BUCKET_NAME="sagemaker-projects-templates-${AWS_ACCOUNT_ID}-${AWS_REGION}"
export DOMAIN_ID="<your sagemaker domain>"
```

### 0. GitHub Repository Naming Requirement

Your GitHub repository name **must start with `sagemaker-`** (e.g., `sagemaker-modelops-project`).

This is required for the **AmazonSageMakerProjectsLaunchRole** (more details about this role in [Step 4](#4-required-iam-roles-and-policies-only-once-and-used-for-all-custom-templates)) to associate your GitHub repository with the SageMaker project.

> 💡 **Recommendation:** Create a new repository specifically for this project.

### 1. AWS CodeConnection Setup
Create a CodeConnection to your GitHub account following [this guide](https://docs.aws.amazon.com/dtconsole/latest/userguide/connections-create-github.html).

Your CodeConnection ARN will look like:
```
arn:aws:codeconnections:<REGION>:<ACCOUNT_ID>:connection/aEXAMPLE-8aad-4d5d-8878-dfcab0bc441f
```

Add the following tag to your connection 
```
key=sagemaker value=true
```

![](./images/code-connection.png)

In the above example, `aEXAMPLE-8aad-4d5d-8878-dfcab0bc441f` is the unique ID for this connection. We use this ID when we create our SageMaker project later in this example.

### 2. GitHub Personal Access Token
Create a GitHub personal access token with access to **Contents** and **Actions** permissions, following the instructions on [Managing your personal access tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)

> Note: You can create either classic or fine-grained access token. However, make sure the token has access to the Contents and Actions (workflows, runs and artifacts) for that repository.

**[Fine-grained Personal Access Token (Recommended)](https://github.com/settings/personal-access-tokens):**
* Click "Generate new token" → "Fine-grained token"
* Repository access: Select "Only select repositories" → Choose sagemaker-ai-modelops-custom-template #or whatever your repo is
* Permissions:
    * Repository permissions:
        * ✅ Actions: Read and write
        * ✅ Contents: Read and write
        * ✅ Workflows: Read and write
* Click "Generate token"
* Copy the token (you won't see it again!)

**[Classic Personal Access Token](https://github.com/settings/tokens):**
* Click "Generate new token" → "Generate new token (classic)"
* Give it a descriptive name:SageMaker ModelOps Lambda
* Select these scopes:
    * ✅repo(Full control of private repositories) - Required
    * ✅workflow(Update GitHub Action workflows) - Required
* Click "Generate token"

**then store it in AWS Secrets Manager.**

```bash
aws secretsmanager create-secret \
    --name sagemaker-github-token \
    --description "GitHub token for SageMaker ModelOps" \
    --secret-string '{"token":"your-github-token-here"}'
```

### 3. IAM User for GitHub Actions
To allow GitHub Actions to deploy SageMaker endpoints in your AWS environment, you need to create an [AWS Identity and Access Management](https://aws.amazon.com/iam/) (IAM) user and grant it the necessary permissions. For instructions and best practices, refer to [Creating an IAM user in your AWS account](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html). 
Create an IAM user with the policy from [`iam/GithubActionsMLOpsExecutionPolicy.json`](./iam/GithubActionsMLOpsExecutionPolicy.json) and generate access keys for GitHub Secrets.
```bash
aws iam create-user --user-name sagemaker-github-actions-user
```
```bash
aws iam create-policy \
    --policy-name SageMakerGitHubActionsPolicy \
    --policy-document file://iam/GithubActionsMLOpsExecutionPolicy.json
```

```bash
aws iam attach-user-policy \
    --user-name sagemaker-github-actions-user \
    --policy-arn arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/SageMakerGitHubActionsPolicy
```

```bash
aws iam create-access-key --user-name sagemaker-github-actions-user
```

Take note of the generated `access key` and `secret access key`, as you will need it in the subsequent step when configuring your GitHub secrets.

### 4. Required IAM Roles and Policies (only once and used for all custom templates)

These are service-specific execution roles that AWS services assume to perform their designated tasks within your ModelOps pipeline:

- **AmazonSageMakerProjectsCloudformationRole** - Role for CloudFormation to manage SageMaker resources
- **AmazonSageMakerProjectsCodeBuildRole** - Role for CodeBuild projects to build and push container images
- **AmazonSageMakerProjectsCodePipelineRole** - Role for CodePipeline to orchestrate CI/CD workflows
- **AmazonSageMakerProjectsExecutionRole** - Role for SageMaker training and inference jobs
- **AmazonSageMakerProjectsLambdaRole** - Role for Lambda functions used in ModelOps workflows
- **AmazonSageMakerProjectsUseRole** - General-purpose role for various SageMaker project services

Each AWS service (CodePipeline, CodeBuild, etc.) assumes its corresponding Use Role to perform only the actions it needs, following the principle of least 
privilege.

#### Launch Role

**AmazonSageMakerProjectsLaunchRole** is a provisioning role that acts as an intermediary during project creation:

- **Purpose**: Contains all permissions needed to create the project's infrastructure (IAM roles, S3 buckets, CodePipeline, etc.)
- **Benefit**: ML engineers and data scientists can create projects without having broader permissions
- **Security**: Their personal SageMaker Execution Role remains limited - they just need permission to assume the Launch Role itself

#### Why This Separation Matters

Without Launch Roles, every ML practitioner would need extensive IAM permissions to create CodePipeline, CodeBuild projects, S3 buckets, and other AWS resources. 
With Launch Roles, they only need permission to assume a pre-configured role that handles the provisioning, keeping their personal permissions minimal and secure.

Lets identify the SageMaker Execution role of the SageMaker user profile.
We intend to grant him permissions to deploy the provisioned custom template. Make sure to `<DOMAIN-ID>` with your actual SageMaker AI domain

```bash
export SAGEMAKER_EXECUTION_ROLE_ARN=$(aws sagemaker describe-domain --domain-id $DOMAIN_ID --query 'DefaultUserSettings.ExecutionRole' --output text)
```

```bash
aws cloudformation deploy \
  --template-file iam/sagemaker-projects-roles-and-policies.yaml \
  --stack-name sagemaker-projects-roles-policies \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides SageMakerExecutionRoleArn=$SAGEMAKER_EXECUTION_ROLE_ARN \
  --region $AWS_REGION
```

This creates the necessary launch and execution roles that SageMaker projects require to provision resources securely.


### 4a. Additional Permissions
**SageMaker Execution Role**

Permission to `iam:PassRole` to `AmazonSageMakerProjectsLaunchRole`

```bash
cat > iam/pass-role-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/AmazonSageMakerProjectsLaunchRole"
    }
  ]
}
EOF
```

```bash
aws iam put-role-policy \
  --role-name $(echo $SAGEMAKER_EXECUTION_ROLE_ARN | cut -d'/' -f3) \
  --policy-name SageMakerProjectsPassRolePolicy \
  --policy-document file://iam/pass-role-policy.json
```

Permission to create CloudFormation Stacks
```bash
aws iam put-role-policy \
  --role-name $(echo $SAGEMAKER_EXECUTION_ROLE_ARN | cut -d'/' -f3) \
  --policy-name SageMakerProjectsCreateCFNTemplates \
  --policy-document file://iam/cfn-stack-sm-projects.json
```
**S3 Tagging (optional)**
The default SageMaker execution role may be missing `s3:GetObjectTagging` permissions required by some templates. Add this permission:

```bash
aws iam put-role-policy \
  --role-name $(echo $SAGEMAKER_EXECUTION_ROLE_ARN | cut -d'/' -f3) \
  --policy-name SageMakerS3GetObjectTaggingPolicy \
  --policy-document file://iam/s3-tagging-policy.json
```

- **[sagemaker-projects-roles-and-policies.yaml](./iam/sagemaker-projects-roles-and-policies.yaml)** - Contains the necessary IAM roles and policies required by these templates
- **[s3-tagging-policy.json](./iam/s3-tagging-policy.json)** - Additional S3 GetObjectTagging policy for SageMaker buckets
- **[cfn-stack-sm-projects.json](./iam/cfn-stack-sm-projects.json)** - CloudFormation permissions policy allowing SageMaker execution role to create and manage CloudFormation stacks for SageMaker AI Projects

### 5. Create S3 Bucket

```bash
aws s3 mb s3://$BUCKET_NAME --region $AWS_REGION
```

#### Configure CORS Policy

Create a CORS policy file (`cors-policy.json`):

```json
{
    "CORSRules": [
        {
            "AllowedHeaders": [
                "*"
            ],
            "AllowedMethods": [
                "POST",
                "PUT",
                "GET",
                "HEAD",
                "DELETE"
            ],
            "AllowedOrigins": [
                "https://*.sagemaker.aws"
            ],
            "ExposeHeaders": [
                "ETag",
                "x-amz-delete-marker",
                "x-amz-id-2",
                "x-amz-request-id",
                "x-amz-server-side-encryption",
                "x-amz-version-id"
            ]
        }
    ]
}
```

Apply the CORS policy:

```bash
aws s3api put-bucket-cors --bucket $BUCKET_NAME --cors-configuration file://cors-policy.json
```

> 💡 **Tip:** you can also let SageMaker AI apply the CORS coffiguration to the bucket for you see **Configure SageMaker Domain** in [S3 Upload and Tagging](#s3-upload-and-tagging))

### 6. Deploy Lambda Function

This lambda will trigger the deploy GitHub action on model registry approval

```bash
chmod +x scripts/deploy-lambda.sh
./scripts/deploy-lambda.sh $BUCKET_NAME $AWS_REGION 
```

### 7. GitHub Repository Setup

#### Repository Structure
Copy the contents of the `seedcode/` directory to the root of your GitHub repository, inluding `.github/workflows` (see the following screenshot):
```
your-repo/
├── .github/
│   └── workflows/
│       ├── build.yml
│       └── deploy.yml
├── pipelines/
├── tests/
├── build_deployment_configs.py
├── deploy_stack.py
└── ... (other seedcode files)
```
![](./images/repo-structure.png)

#### GitHub Secrets containing the IAM user access keys
In this step, we store the access key details of the user created in [step 3](#3-iam-user-for-github-actions) in our [GitHub repository secrets](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets#creating-secrets-for-a-repository).
Add these secrets to your GitHub repository as follows:
1. On the GitHub website, navigate to your repository and choose **Settings**.
2. In the **security** section of the sidebar, select **Secrets and Variables**, then click **Actions**.
3. Click the **Secrets** tab and choose **New Repository Secret**.
4. In the Name field, type `AWS_ACCESS_KEY_ID`
5. In the Secret field, enter the access key ID associated with the IAM user you created in [step 3](#3-iam-user-for-github-actions).
6. Click Add secret.
7. Repeat the same procedure for `AWS_SECRET_ACCESS_KEY`

#### Create GitHub Environment
To create a manual approval step in our deployment pipelines, we use a [GitHub environment](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments). Complete the following steps:
1. Go to your repository **Settings** > **Environments**
2. Create environment named `production`
3. Add required reviewers for deployment approval. These are the people who can approve model deployment to production environment
   ![](./images/reviewer.png)

## Template Deployment

### S3 Upload and Tagging

1. **Upload template to S3:**
```bash
aws s3 cp template.yaml s3://$BUCKET_NAME/templates/mlops-github-actions.yaml
```

2. **Tag for SageMaker visibility:**
```bash
aws s3api put-object-tagging \
    --bucket $BUCKET_NAME \
    --key templates/mlops-github-actions.yaml \
    --tagging 'TagSet=[{Key=sagemaker:studio-visibility,Value=true}]'
```
![](./images/s3-tag.png)

3. **Configure SageMaker Domain:**
```bash
aws sagemaker add-tags --resource-arn arn:aws:sagemaker:$AWS_REGION:$AWS_ACCOUNT_ID:domain/$DOMAIN_ID --tags Key=sagemaker:projectS3TemplatesLocation,Value=s3://$BUCKET_NAME/templates/
```

![](./images/domain-tag.png)

4. **Let SageMaker add CORS to your bucket** (optional if you did it in step [5](#configure-cors-policy))
![](./images/cors.png)

## Create the project with these template Parameters

| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| `SageMakerProjectName` | Name of the SageMaker project | Yes | - |
| `Role ARN` | AmazonSageMakerProjectsLaunchRole (ARN) | Yes | - |
| `CodeRepositoryName` | GitHub repository name | Yes | - |
| `GitHubRepositoryOwnerName` | GitHub username or organization | Yes | - |
| `CodestarConnectionUniqueId` | CodeConnection ID | Yes | - |
| `GitHubTokenSecretName` | Secrets Manager secret name | Yes | - |
| `GitHubWorkflowNameForDeployment` | Deployment workflow filename | Yes | deploy.yml |
| `LambdaS3Bucket` | Name of the S3 bucket with Lambda function (Not the S3 URI) | Yes | - |
| `LambdaS3Key` | Lambda function S3 key | Yes | lambda-github-workflow-trigger.zip |

### Method 1: Using SageMaker Studio

1. Open SageMaker Studio
2. Navigate to **More** > **Projects** > **Create project**
3. Choose **Organization templates** > **S3 Templates** . Select **MLOps GitHub Actions** template as shown below:
   ![](./images/modelops_project.png)

To launch the ModelOps project, you must enter project-specific details including the `Role ARN` field. This field should contain the `AmazonSageMakerProjectsLaunchRole ARN` created during setup, as shown in the following image.

As a security best practice, use the `AmazonSageMakerProjectsLaunchRole Amazon Resource Name (ARN)`, not your SageMaker execution role.

The AmazonSageMakerProjectsLaunchRole is a provisioning role that acts as an intermediary during the ModelOps project creation. This role contains all the permissions needed to create your project’s infrastructure, including [IAM](https://aws.amazon.com/iam/) roles, S3 buckets, [AWS CodePipeline](https://aws.amazon.com/fr/codepipeline/), and other AWS resources. By using this dedicated launch role, ML engineers and data scientists can create ModelOps projects without requiring broader permissions in their own accounts. Their personal SageMaker execution role remains limited in scope—they only need permission to assume the launch role itself.

This separation of responsibilities is important for maintaining security. Without launch roles, every ML practitioner would need extensive IAM permissions to create code pipelines, [AWS CodeBuild](https://aws.amazon.com/codebuild) projects, S3 buckets, and other AWS resources directly. With launch roles, they only need permission to assume a pre-configured role that handles the provisioning on their behalf, keeping their personal permissions minimal and secure.

5. Fill in the project configuration details and choose Next. T
   ![](./images/project_details.png)
   
### Method 2: Python SDK

```python
import boto3

sagemaker_client = boto3.client('sagemaker', region_name='us-west-2')

response = sagemaker_client.create_project(
    ProjectName='modelOps-github-actions-project',
    ProjectDescription='ModelOps project using SageMaker and GitHub Actions',
    TemplateProviders=[{
        'CfnTemplateProvider': {
            'TemplateName': 'MLOpsGitHubActions',
            'TemplateURL': 'https://your-bucket.s3.region.amazonaws.com/mlops-github-actions/template.yaml',
            'Parameters': [
                {'Key': 'CodeRepositoryName', 'Value': 'your-repo-name'},
                {'Key': 'GitHubRepositoryOwnerName', 'Value': 'your-github-username'},
                {'Key': 'CodestarConnectionUniqueId', 'Value': 'your-connection-id'},
                {'Key': 'GitHubTokenSecretName', 'Value': 'your-secret-name'},
                {'Key': 'LambdaS3Bucket', 'Value': 'your-lambda-bucket'},
                {'Key': 'LambdaS3Key', 'Value': 'lambda-github-workflow-trigger.zip'}
            ]
        }
    }]
)
```
## Post-Deployment Configuration

After creating the project:

1. **Update GitHub Workflow Variables:**
   Edit `.github/workflows/build.yml` and `.github/workflows/deploy.yml`:
   ```yaml
   env:
     AWS_REGION: <REGION>  # Your AWS region
     SAGEMAKER_PROJECT_NAME: your-project-name  # Your project name
   ```

2. **Test the Pipeline:**
   - Make changes to the `pipelines/abalone/pipeline.py` file
   - Push to your GitHub repository
   - Verify the build workflow runs automatically
   - Approve a model in SageMaker Model Registry
   - Verify the deployment workflow triggers
   
The template will then create two automated ModelOps workflows—one for model building and one for model deployment—that work together to provide CI/CD for your ML models. 

   ![](./images/sagemaker_pipeline.png)
  
## Clean up
After deployment, you will incur costs for the deployed resources. If you don’t intend to continue using the setup, delete the ModelOps project resources to avoid unnecessary charges.

To destroy the project, open SageMaker Studio and choose **More** in the navigation pane and select **Projects**. Choose the project you want to delete, choose the vertical ellipsis above the upper-right corner of the projects list and choose **Delete**. Review the information in the Delete project dialog box and select **Yes, delete the project** to confirm. After deletion, verify that your project no longer appears in the projects list.

In addition to deleting a project, which will remove and deprovision the SageMaker AI Project, you also need to manually delete the following components if they’re no longer needed: Git repositories, pipelines, model groups, and endpoints.

## Troubleshooting

### Template Not Visible in SageMaker Studio
- Verify the `sagemaker:studio-visibility` tag is set to `true`
- Check that the SageMaker domain is tagged with the correct S3 location
- Ensure proper CORS configuration on the S3 bucket

### Lambda Function Errors
- Verify the Lambda function zip file is uploaded to the correct S3 location
- Review CloudWatch logs for detailed error messages

### GitHub Workflow Not Triggering
- Verify the GitHub token has proper permissions
- Check that the secret name matches the parameter value
- Ensure the EventBridge rule is enabled and properly configured

## Security Best Practices

1. **Use least-privilege IAM roles**
3. **Rotate GitHub tokens regularly**

## Resources

- [Original Service Catalog Template](https://github.com/aws-samples/mlops-sagemaker-github-actions)
- [SageMaker Projects Documentation](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-projects.html)
- [S3-Based Templates Guide](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-projects-templates-custom.html)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## License

This template is licensed under the MIT-0 License. See the LICENSE file for details.
