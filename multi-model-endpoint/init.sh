#!/bin/bash

AWS_BUCKET=$1
FILENAME="multi-model-endpoint-seedcode.zip"
SEEDCODE_PATH="awsome-sagemaker-projects-templates/seedcodes"
FULL_PATH="$SEEDCODE_PATH/$FILENAME"

echo $FULL_PATH

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

sed -i "" "s/<#####BUCKET-PLACEHOLDER#####>/$AWS_BUCKET/" "./template.yml"
sed -i "" "s|<#####FILE-PATH-PLACEHOLDER#####>|$FULL_PATH|" "./template.yml"
echo "Update of the template file complete."