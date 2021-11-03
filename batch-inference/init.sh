#!/bin/bash

# INPUTS 
AWS_BUCKET=$1

# SERVICE CATALOG INFORMATION
SERVICE_CATALOG_NAME="SageMaker MLOps Templates"

# SEEDCODE INFO
FILENAME="batch-inference-seedcode.zip"
SEEDCODE_PATH="awsome-sagemaker-projects-templates/seedcodes"
TEMPLATE_URL="https://s3.amazonaws.com/$AWS_BUCKET/$SEEDCODE_PATH/template/template.yml"
FULL_PATH="$SEEDCODE_PATH/$FILENAME"

if [ -z "$1" ]
then
    echo "[ERROR] Please run sh init.sh <BUCKET_NAME>"
    exit
fi

mkdir -p outputs
cd seedcode; zip -qr9 ../outputs/$FILENAME .

cd ../
aws s3 cp outputs/$FILENAME s3://$AWS_BUCKET/$SEEDCODE_PATH/$FILENAME
echo "Upload successful."

sed -i "" "s|<#####BUCKET-PLACEHOLDER#####>|$AWS_BUCKET|" "./template.yml"
sed -i "" "s|<#####FILE-PATH-PLACEHOLDER#####>|$FULL_PATH|" "./template.yml"
echo "Update of the template file complete."
