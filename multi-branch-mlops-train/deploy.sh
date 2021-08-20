#!/bin/bash

if ! command -v aws &> /dev/null
then
    echo "Please install the AWS CLI"
    exit
fi

while getopts m:p:* flag
do
    case "${flag}" in
        m) modelname=${OPTARG};;
        p) pipeline=${OPTARG};;
    esac
done

account_id=$(aws sts get-caller-identity | jq '.Account' -r)
region=$(aws configure get region)

aws cloudformation deploy \
  --stack-name train-baseline \
  --template-file cloud_formation/baseline.yaml

if [ "$pipeline" = "code_pipeline+code_commit" ]
then
  aws cloudformation package \
    --template-file cloud_formation/train-codepipeline-codecommit.yaml \
    --s3-bucket cloud-formation-"$account_id"-"$region" \
    --output-template-file stack-packaged.yaml

  aws cloudformation deploy \
    --stack-name "$modelname"-train \
    --template-file stack-packaged.yaml \
    --parameter-overrides ModelName="$modelname" \
    --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND CAPABILITY_NAMED_IAM

  aws s3 cp cloud_formation/pipeline.yaml s3://model-pipeline-scripts-"$modelname"-"$region"-"$account_id"/pipeline.yaml

  aws cloudformation describe-stacks --stack-name "$modelname"-train --query Stacks[].Outputs[*].[OutputKey,OutputValue] --output text
elif [ "$pipeline" == "jenkins" ]
then
  aws cloudformation package \
    --template-file cloud_formation/train-jenkins.yaml \
    --s3-bucket cloud-formation-"$account_id"-"$region" \
    --output-template-file stack-packaged.yaml

  aws cloudformation deploy \
    --stack-name "$modelname"-train \
    --template-file stack-packaged.yaml \
    --parameter-overrides ModelName="$modelname" \
    --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND CAPABILITY_NAMED_IAM
fi
