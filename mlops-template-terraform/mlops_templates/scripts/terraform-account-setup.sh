#!/bin/bash
STACK_NAME="mlops-tf-bootstrap"
AWS_ACCOUNT=$(aws sts get-caller-identity --query "Account" --output text)
AWS_REGION=${AWS_REGION:-$(aws configure get region)}

# Deploy bucket for state files
bootstrap() {
    echo "---------------------BOOTSTRAPPING---------------------"
    aws cloudformation deploy --template ./scripts/bootstrap/bootstrap_cfn.yaml --stack-name $STACK_NAME
    export BUCKET_NAME=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='BucketName'].OutputValue" --output text)
    export BUCKET_REGION=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='BucketRegion'].OutputValue" --output text)

    # Update provider.tf to use bucket and region
    envsubst < "./scripts/bootstrap/provider.template" > "./terraform/provider.tf"

    # Re-initialize terraform 
    terraform init -reconfigure || true
    echo "State Bucket: $BUCKET_NAME"
    echo "State Region: $BUCKET_REGION"
    echo "-----------------------COMPLETE------------------------"
    echo "Ensure to set your AWS_REGION environment variable to $AWS_REGION for Terrform to select the correct region"
}


read -r -p "Bootstrap $AWS_ACCOUNT in $AWS_REGION?? [Y/n] " CONFIRMATION
case "$CONFIRMATION" in
    [yY][eE][sS]|[yY]) 
       # Deploy bucket for state files
        bootstrap
        ;;
    *)
        echo "Skipping bootstrap"
        ;;
esac
 