#!/bin/bash

# Deploy Lambda function for MLOps GitHub Actions template
# Usage: ./deploy-lambda.sh <s3-bucket> [aws-region]

set -e

# Check if bucket name is provided
if [ $# -lt 1 ]; then
    echo "Usage: $0  [aws-region]"
    echo "Example: $0 my-sagemaker-templates us-west-2"
    exit 1
fi

S3_BUCKET=$1
AWS_REGION=${2:-us-west-2}

echo "Deploying Lambda function to S3 bucket: $S3_BUCKET"
echo "AWS Region: $AWS_REGION"

# Navigate to lambda functions directory
SCRIPT_DIR="$(dirname "$0")"
cd "$SCRIPT_DIR/../lambda_functions"

# Create temporary build directory
BUILD_DIR="/tmp/lambda_build_$(date +%s)"
mkdir -p "$BUILD_DIR"

echo "Installing PyGithub dependencies for arm64..."

# Install dependencies for arm64 platform
pip3 install \
    --platform manylinux2014_aarch64 \
    --target="$BUILD_DIR" \
    --python-version 3.12 \
    --implementation cp \
    --only-binary=:all: \
    PyGithub

# Copy Lambda function code
echo "Copying Lambda function code..."
cp lambda_function.py "$BUILD_DIR/"

# Create zip file
echo "Creating Lambda deployment package..."
cd "$BUILD_DIR"
zip -r lambda-github-workflow-trigger.zip . -x "*.pyc" "**/__pycache__/*"

# Upload to S3
echo "Uploading Lambda function to S3..."
aws s3 cp lambda-github-workflow-trigger.zip "s3://$S3_BUCKET/lambda-github-workflow-trigger.zip" --region "$AWS_REGION"

# Store the zip file locally (optional)
cp lambda-github-workflow-trigger.zip "$SCRIPT_DIR/../lambda_functions/"

echo ""
echo "✅ Deployment complete!"
echo "S3 Location: s3://$S3_BUCKET/lambda-github-workflow-trigger.zip"
echo "Package size: $(du -h lambda-github-workflow-trigger.zip | cut -f1)"

# Cleanup
echo "Cleaning up temporary files..."
cd - &gt; /dev/null
rm -rf "$BUILD_DIR"

echo ""
echo "✅ Deployment complete!"