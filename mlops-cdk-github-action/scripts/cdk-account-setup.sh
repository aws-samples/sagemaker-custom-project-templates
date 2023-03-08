#!/bin/bash
# This script setups the aws accounts with the required permissions for CDK deployments, the account is bootstrapped

read -p 'AWS Account (12-digits): ' dev_account
read -p 'Deployment region (aws regions i.e. us-east-1): ' region

echo 'Updating .env file with accounts and region details'
pattern="[0-9a-zA-Z\-]*"
sed -i '' -e "s/^AWS_ACCOUNT=\"$pattern\"/AWS_ACCOUNT=\"$dev_account\"/" \
            -e "s/^AWS_REGION=\"$pattern\"/AWS_REGION=\"$region\"/" \
            ../.env

echo 'AWS profiles to be used for each account'
read -p 'Account AWS Profile: ' dev_profile

cdk bootstrap aws://$dev_account/$region --cloudformation-execution-policies 'arn:aws:iam::aws:policy/AdministratorAccess' --profile $dev_profile