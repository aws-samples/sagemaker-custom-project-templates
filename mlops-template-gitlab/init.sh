#!/bin/bash

AWS_BUCKET=$1
SECRET_NAME=$2
SECRET_KEY=$3


mkdir -p zip_files
(cd seedcode/mlops-gitlab-project-seedcode-model-deploy ; zip -r ../../zip_files/mlops-gitlab-project-seedcode-model-deploy.zip . -x ../mlops-gitlab-project-seedcode-model-deploy)
(cd seedcode/mlops-gitlab-project-seedcode-model-build ; zip -r ../../zip_files/mlops-gitlab-project-seedcode-model-build.zip . -x ../mlops-gitlab-project-seedcode-model-build)

(cd lambda_functions/lambda-gitlab-pipeline-trigger ; zip -r ../../zip_files/lambda-gitlab-pipeline-trigger.zip . -x ../lambda-gitlab-pipeline-trigger)
(cd lambda_functions/lambda-seedcode-checkin-gitlab ; zip -r ../../zip_files/lambda-seedcode-checkin-gitlab.zip . -x ../lambda-seedcode-checkin-gitlab)

# Upload files to S3

cd zip_files
for filename in *.zip; do
    aws s3 cp $filename s3://$AWS_BUCKET/gitlab-project/$filename
done

# Create secret in Secrets Manager
aws secretsmanager create-secret --name $SECRET_NAME --secret-string $SECRET_KEY