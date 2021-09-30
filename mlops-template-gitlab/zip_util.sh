#!/bin/bash


(cd seedcode ; zip -r ../zip_files/mlops-gitlab-project-seedcode-model-deploy.zip . -x ../mlops-gitlab-project-seedcode-model-deploy)
(cd seedcode ; zip -r ../zip_files/mlops-gitlab-project-seedcode-model-build.zip . -x ../mlops-gitlab-project-seedcode-model-build)

(cd lambda_functions ; zip -r ../zip_files/lambda-gitlab-pipeline-trigger.zip . -x ../lambda-gitlab-pipeline-trigger)
(cd lambda_functions ; zip -r ../zip_files/lambda-seedcode-checkin-gitlab.zip . -x ../lambda-seedcode-checkin-gitlab)

# Upload files to S3

cd zip_files
for filename in *.zip; do
    aws s3 cp $filename s3://sagemaker-us-east-2-682101512330/gitlab-project/$filename
done