#!/bin/bash

if ! command -v aws &> /dev/null
then
    echo "Please install the AWS CLI"
    exit
fi

while getopts p:* flag
do
    case "${flag}" in
        p) pipeline=${OPTARG};;
    esac
done

account_id=$(aws sts get-caller-identity | jq '.Account' -r)
region=$(aws configure get region)

aws cloudformation deploy \
  --stack-name train-baseline \
  --template-file cloud_formation/baseline.yaml \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM

if [ "$pipeline" = "code_pipeline+code_commit" ]
then
  aws cloudformation package \
    --template-file cloud_formation/train-codepipeline-codecommit.yaml \
    --s3-bucket cloud-formation-"$account_id"-"$region" \
    --output-template-file cloud_formation/model_train.yaml

  aws s3 cp cloud_formation/pipeline.yaml s3://cloud-formation-"$account_id"-"$region"/pipeline.yaml
  aws s3 cp cloud_formation/model_train.yaml s3://cloud-formation-"$account_id"-"$region"/model_train.yaml
elif [ "$pipeline" == "jenkins" ]
then
  aws cloudformation package \
    --template-file cloud_formation/train-jenkins.yaml \
    --s3-bucket cloud-formation-"$account_id"-"$region" \
    --output-template-file cloud_formation/model_train.yaml

  aws s3 cp cloud_formation/model_train.yaml s3://cloud-formation-"$account_id"-"$region"/model_train.yaml
fi
