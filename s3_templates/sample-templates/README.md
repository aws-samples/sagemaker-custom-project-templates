# SageMaker Projects Provided Templates

This folder contains 5 SageMaker project templates that are normally available through AWS Service Catalog in SageMaker AI Studio.
The original templates are provided and supported by the SageMaker Service Team. They can be deployed as custom templates.

## Available Templates

1. **[Model building and training with third-party Git using CodePipeline](./build-train-codepipeline.yaml)** - Basic MLOps template for model training with CodePipeline
2. **[Model building, training, and deployment with third-party Git repositories using CodePipeline](./build-train-deploy-codepipeline.yaml)** - Complete MLOps template for training and deployment with AWS CodePipeline  
3. **[Model building, training, and deployment with third-party Git repositories using Jenkins](./build-train-deploy-jenkins.yaml)** - MLOps template using Jenkins for CI/CD
4. **[Model building, training, deployment and monitoring with third-party git using CodePipeline](./build-train-deploy-monitor-codepipeline.yaml)** - Advanced MLOps template with model monitoring
5. **[Model deployment with third-party Git using CodePipeline](./deploy-codepipeline.yaml)** - Model deployment pipeline template

Detailed information about these templates and how to use them is provided in the [docs](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-projects-templates-sm.html)

## When to Use These Templates

Use these templates when:
- You want to customize the official SageMaker templates
- You need to deploy SageMaker's standard MLOps patterns as custom templates

## Provisioning the templates (only once)

These templates can be deployed using the S3 provisioning model.
Upload the desired template(s) to your S3 bucket and configure your SageMaker domain to use them as custom project templates.

### 1. Upload Templates and Tag for Visibility

Upload your template files to the S3 bucket:

```bash
for file in templates/*.yaml; do
  aws s3 cp "$file" s3://$BUCKET_NAME/templates/ && \
  aws s3api put-object-tagging --bucket $BUCKET_NAME --key "$file" --tagging 'TagSet=[{Key=sagemaker:studio-visibility,Value=true}]'
done
```

Verify the templates are visible in the SageMaker AI Studio console

![](./images/sm-projects-custom-template-s3.png)

### 2. Required IAM Roles and Policies

SageMaker Projects require a set of IAM roles that fall under two categories:

* `Use Roles` – Used within the template by each resource for the required operations. For each operation in the product template, the Use Role is assumed by the respective AWS Service Principal.
* `Launch Role` – Used to define permissions to provision the underlying resources specified by the template. This allows developers to create projects using templates without needing their SageMaker Execution Role to have all the policies needed. SageMaker Projects uses the launch role while creating the project so that the developers using the project can have their roles limited to the specific policies they need.

These are roles and policies assumed by the underlying services, e.g., AWS CodePipelines, AWS CodeBuild, AWS Lambda, to allow them to perform the actions needed.
Here are the list of service roles defined by this template:

- **AmazonSageMakerProjectsCloudformationRole** - Role for CloudFormation to manage SageMaker resources
- **AmazonSageMakerProjectsCodeBuildRole** - Role for CodeBuild projects to build and push container images
- **AmazonSageMakerProjectsCodePipelineRole** - Role for CodePipeline to orchestrate CI/CD workflows
- **AmazonSageMakerProjectsExecutionRole** - Role for SageMaker training and inference jobs
- **AmazonSageMakerProjectsLambdaRole** - Role for Lambda functions used in MLOps workflows
- **AmazonSageMakerProjectsUseRole** - General-purpose role for various SageMaker project services

Furthermore, it defines a "Launch Role" (**AmazonSageMakerProjectsLaunchRole**) that the SageMaker Execution role can assume.
In this way, the Launch Role encapsulates all necessary permissions without the need to extend the scope of the SageMaker Execution role directly.

Lets identify the SageMaker Execution role of the SageMaker user profile.
We intend to grant him permissions to deploy the provisioned custom template.

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


### 2a. Additional Permissions
**SageMaker Execution Role**

Permission to `iam:PassRole` to `AmazonSageMakerProjectsLaunchRole`**

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

## Launch a custom template

### AWS Console (Studio)
1. Open SageMaker Studio
2. Navigate to **Deployments** > **Projects** > **Create project**
3. Choose **Organization templates** > **S3 Templates**
4. Select your template and click **Next**
5. Enter project details - make sure that in the `Role ARN` field, you pass the ARN of the **AmazonSageMakerProjectsLaunchRole**
![](./images/LaunchRole.png)
6. Click **Create**.

### Python SDK
```python
import boto3

sagemaker_client = boto3.client('sagemaker', region_name='us-east-1')

response = sagemaker_client.create_project(
    ProjectName='my-custom-project',
    ProjectDescription='SageMaker project with custom CFN template stored in S3',
    TemplateProviders=[{
        'CfnTemplateProvider': {
            'TemplateName': 'CustomProjectTemplate',
            'TemplateURL': f'https://{BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/templates/custom-project-template.yml',
            'Parameters': [
                {'Key': 'ParameterKey', 'Value': 'ParameterValue'}
            ]
        }
    }]
)
print(f"Project ARN: {response['ProjectArn']}")
```