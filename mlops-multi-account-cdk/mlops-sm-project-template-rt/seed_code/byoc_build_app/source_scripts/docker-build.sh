#!/bin/bash

REPO_NAME=$1

echo $REPO_NAME

aws ecr describe-repositories --region $AWS_DEFAULT_REGION --repository-names $REPO_NAME | jq --raw-output '.repositories[0]' > repository-info.json;

AWS_ACCOUNT_ID=$(jq -r .registryId repository-info.json);
REPOSITORY_URI=${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/${REPO_NAME};
# REPOSITORY_URI=local

aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login  --username AWS  --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com

target_stages=("processing" "training")

for stage in "${target_stages[@]}"
do

        IMAGE_TAG=$stage-$CODEBUILD_RESOLVED_SOURCE_VERSION;

        echo $IMAGE_TAG

        docker build --target $stage -t $REPOSITORY_URI:$stage .
        docker tag $REPOSITORY_URI:$stage $REPOSITORY_URI:$IMAGE_TAG

        docker push $REPOSITORY_URI:$stage
        docker push $REPOSITORY_URI:$IMAGE_TAG

done
