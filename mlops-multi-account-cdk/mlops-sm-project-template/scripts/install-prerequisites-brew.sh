#!/bin/bash
# this script uses Homebrew to do the installations for all prerequisites to deploy the solution described in this repository

# install miniconda to manage python packages
brew install --cask miniconda

# conda doesn't initialize from shell, below step to fix that
# https://github.com/conda/conda/issues/7980
CONDA_BASE=$(conda info --base)
source "$CONDA_BASE"/etc/profile.d/conda.sh
conda init

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
