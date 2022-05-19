#!/bin/bash
# This script setups the aws accounts with the required permissions for CDK deployments, the accounts are bootstrapped
# and configured to enable cross account access as per the architecture diagram

read -p 'Governance Account: ' gov_account
read -p 'Dev Account: ' dev_account
read -p 'PreProd Account: ' preprod_account
read -p 'Prod Account: ' prod_account

region='eu-west-1'

read -p 'Deployment region: ' region

echo 'AWS profiles to be used for each account'
read -p 'Governance Account AWS Profile: ' gov_profile
read -p 'Dev Account AWS Profile: ' dev_profile
read -p 'PreProd Account AWS Profile: ' preprod_profile
read -p 'Prod Account AWS Profile: ' prod_profile

pip install -r requirements.txt

cdk bootstrap aws://$gov_account/$region --profile $gov_profile

cdk bootstrap aws://$dev_account/$region --trust $gov_profile --cloudformation-execution-policies 'arn:aws:iam::aws:policy/AdministratorAccess' --profile $dev_profile

cdk bootstrap aws://$preprod_account/$region --trust $dev_account $gov_profile --cloudformation-execution-policies 'arn:aws:iam::aws:policy/AdministratorAccess' --profile $preprod_profile

cdk bootstrap aws://$prod_account/$region --trust $dev_account $gov_profile --cloudformation-execution-policies 'arn:aws:iam::aws:policy/AdministratorAccess' --profile $prod_profile
