#!/bin/bash

sudo yum install -y gettext wget unzip jq

export TERRAFORM_VERSION="1.2.4"

echo "Attempting to install terraform" && \
wget -q https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip -P /tmp && \
unzip -q /tmp/terraform_${TERRAFORM_VERSION}_linux_amd64.zip -d /tmp && \
sudo mv /tmp/terraform /usr/local/bin/ && \
rm -rf /tmp/terraform_${TERRAFORM_VERSION}_linux_amd64.zip && \
echo "terraform is installed successfully"

FOLDER_NAME=$(basename "$PWD")

# Read the SM_PROJECT_ID from the folder name
DEFAULT_SM_PROJECT_ID=$(cat .sagemaker-code-config | jq -r .sagemakerProjectId)
read -p "Sagemaker Project ID (default \"$DEFAULT_SM_PROJECT_ID\"): " sm_project_id_input
export SM_PROJECT_ID="${sm_project_id_input:-$DEFAULT_SM_PROJECT_ID}"

if [[ -z $SM_PROJECT_ID ]]; then
    echo "No Sagemaker Project ID provided"
    exit 1
fi

# Read the SM_PROJECT_NAME from the folder name
DEFAULT_SM_PROJECT_NAME=$(cat .sagemaker-code-config | jq -r .sagemakerProjectName)
read -p "Sagemaker Project ID (default \"$DEFAULT_SM_PROJECT_NAME\"): " sm_project_id_input
export SM_PROJECT_NAME="${sm_project_id_input:-$DEFAULT_SM_PROJECT_NAME}"

if [[ -z $SM_PROJECT_NAME ]]; then
    echo "No Sagemaker Project Name provided"
    exit 1
fi


# Fetch Values from CloudFormation Stack Output
export STACK_NAME=$(aws cloudformation describe-stacks --query 'Stacks[?Tags[?Key == `sagemaker:project-id` && Value == `'$DEFAULT_SM_PROJECT_ID'`]].{StackName: StackName}' --output text)

export PREFIX=$(aws cloudformation describe-stacks --query "Stacks[?StackName=='$STACK_NAME'][].Outputs[?OutputKey=='Prefix'].OutputValue" --output text)

export STATE_BUCKET_NAME=$(aws cloudformation describe-stacks --query "Stacks[?StackName=='$STACK_NAME'][].Outputs[?OutputKey=='MlOpsProjectStateBucket'].OutputValue" --output text)

export ARTIFACT_BUCKET_NAME=$(aws cloudformation describe-stacks --query "Stacks[?StackName=='$STACK_NAME'][].Outputs[?OutputKey=='MlOpsArtifactsBucket'].OutputValue" --output text)

export BUCKET_REGION=$(aws cloudformation describe-stacks --query "Stacks[?StackName=='$STACK_NAME'][].Outputs[?OutputKey=='BucketRegion'].OutputValue" --output text)

CF_DEFAULT_BRANCH=$(aws cloudformation describe-stacks --query "Stacks[?StackName=='$STACK_NAME'][].Outputs[?OutputKey=='DefaultBranch'].OutputValue" --output text)

export DEFAULT_BRANCH=${CF_DEFAULT_BRANCH:-main}


# Get the AWS Account ID. Should be set as environmet variable in SageMaker Studio
read -p "AWS_ACCOUNT_ID (default \"$AWS_ACCOUNT_ID\"): " input_account_id
export AWS_ACCOUNT_ID="${input_account_id:-$AWS_ACCOUNT_ID}"

if [[ -z "$AWS_ACCOUNT_ID" ]]; then
    echo "No AWS_ACCOUNT_ID provided"
    exit 1
fi

# Get the AWS Region ID. Should be set as environmet variable in SageMaker Studio
read -p "AWS_REGION (default \"$AWS_REGION\"): " input_region
export AWS_REGION="${input_region:-$AWS_REGION}"

if [[ -z "$AWS_REGION" ]]; then
    echo "No AWS_REGION provided"
    exit 1
fi

CODECOMMIT_ID=$(cat .sagemaker-code-config | jq -r .codeRepositoryName)
read -p "CODECOMMIT_ID (default \"$CODECOMMIT_ID\"): " input_codecommit_id
export CODECOMMIT_ID="${input_codecommit_id:-$CODECOMMIT_ID}"

if [[ -z "$CODECOMMIT_ID" ]]; then
    echo "No CODECOMMIT_ID provided"
    exit 1
fi

read -p "DEFAULT_BRANCH (default \"$DEFAULT_BRANCH\"): " input_default_branch
export DEFAULT_BRANCH="${input_default_branch:-$DEFAULT_BRANCH}"

if [[ -z "$DEFAULT_BRANCH" ]]; then
    echo "No DEFAULT_BRANCH provided"
    exit 1
fi


export SM_EXECUTION_ROLE_ARN="arn:aws:iam::$AWS_ACCOUNT_ID:role/$PREFIX-sagemaker-execution-role"
export MODEL_PACKAGE_GROUP_NAME="$PREFIX-$SM_PROJECT_NAME-models"

echo "--------------Bootstrap Output-----------------"
echo "Prefix: $PREFIX"
echo "Sagmaker Project ID: $SM_PROJECT_ID"
echo "Sagmaker Name: $SM_PROJECT_NAME"
echo "AWS Account ID: $AWS_ACCOUNT_ID"
echo "AWS Region: $AWS_REGION"
echo "Artifact bucket name: $ARTIFACT_BUCKET_NAME"
echo "State bucket name: $STATE_BUCKET_NAME"
echo "CodeCommit ID: $CODECOMMIT_ID"
echo "Default Branch: $DEFAULT_BRANCH"
echo "SageMaker Execution Role: $SM_EXECUTION_ROLE_ARN"
echo "Model Package Group Name: $MODEL_PACKAGE_GROUP_NAME"
echo "-----------------------------------------------"

# Update provider.tf to use bucket and region
envsubst < "./infra_scripts/bootstrap/provider.template" > "./terraform/provider.tf"

# Update terraform.tfvars
envsubst < "./infra_scripts/bootstrap/terraform.tfvars.template" > "./terraform/terraform.tfvars"

# Update .project.env
SM_CODE_CONFIG=$(cat .sagemaker-code-config)
UPDATED_SM_CODE_CONFIG=$(echo $SM_CODE_CONFIG | jq ".prefix |= \"${PREFIX}\"" | jq ".model_package_group_name |= \"$MODEL_PACKAGE_GROUP_NAME\"" )

echo ${UPDATED_SM_CODE_CONFIG} | jq '.' > .sagemaker-code-config

cd terraform

terraform init

cd ..

echo "Commit & update tfvars, terraform provider and sagemaker-code-config"
git add .sagemaker-code-config
git add terraform/provider.tf 
git add terraform/terraform.tfvars 
git commit --author="SM Projects <>" -m "Bootstrapping complete"
git push
echo "Bootstrapping completed"

