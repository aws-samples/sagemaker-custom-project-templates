#!/bin/bash

AWS_BUCKET=$1
SEEDCODE_PATH="awsome-sagemaker-projects-templates/seedcodes"
BUILD_FILENAME="serverless-inference-build-seedcode.zip"
DEPLOY_FILENAME="serverless-inference-deploy-seedcode.zip"
BUILD_FULL_PATH="$SEEDCODE_PATH/$BUILD_FILENAME"
DEPLOY_FULL_PATH="$SEEDCODE_PATH/$DEPLOY_FILENAME"

echo $BUILD_FULL_PATH
echo $DEPLOY_FULL_PATH

if [ -z "$1" ]
then
    echo "[ERROR] Please run sh init.sh <BUCKET_NAME>"
    exit
fi

mkdir -p outputs
cd seedcode/build; zip -qr9 ../../outputs/$BUILD_FILENAME .
cd ../../
cd seedcode/deploy; zip -qr9 ../../outputs/$DEPLOY_FILENAME .
cd ../../

aws s3 cp outputs/$BUILD_FILENAME s3://$AWS_BUCKET/$SEEDCODE_PATH/$BUILD_FILENAME
aws s3 cp outputs/$DEPLOY_FILENAME s3://$AWS_BUCKET/$SEEDCODE_PATH/$DEPLOY_FILENAME
echo "Upload successful."

sed -i "" "s|<#####BUILD-BUCKET-PLACEHOLDER#####>|$AWS_BUCKET|" "./template.yml"
sed -i "" "s|<#####BUILD-FILE-PATH-PLACEHOLDER#####>|$BUILD_FULL_PATH|" "./template.yml"
sed -i "" "s|<#####DEPLOY-BUCKET-PLACEHOLDER#####>|$AWS_BUCKET|" "./template.yml"
sed -i "" "s|<#####DEPLOY-FILE-PATH-PLACEHOLDER#####>|$DEPLOY_FULL_PATH|" "./template.yml"
echo "Update of the template file complete."