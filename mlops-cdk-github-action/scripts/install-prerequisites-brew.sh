#!/bin/bash
# this script uses Homebrew to do the installations for all prerequisites to deploy the solution described in this repository

# install miniconda to manage python packages
brew install --cask miniconda

# install nodejs (required for aws cdk)
brew install node

# install docker (mainly to handle bundling CDK assets)
brew install --cask docker

# install aws cdk
npm install -g aws-cdk

# setup python environemnt
conda create -n cdk-env python=3.8
conda activate cdk-env

# install aws cli in the python environment
pip install awscli

# now you should have all the necessary packages setup on your machines and should proceed with creating the aws profiles to start setting up the accounts and deploying the solution
