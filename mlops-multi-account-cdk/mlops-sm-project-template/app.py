#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# SPDX-License-Identifier: MIT-0
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import aws_cdk as cdk
import os
import json
from mlops_sm_project_template.pipeline_stack import PipelineStack, CoreStage
from mlops_sm_project_template.codecommit_stack import CodeCommitStack
from mlops_sm_project_template.config.constants import DEFAULT_DEPLOYMENT_REGION, PIPELINE_ACCOUNT


def load_account_set_config(filename):
    """
    Loads config from file
    """

    with open(filename, "r", encoding="utf-8") as f:
        config = json.load(f)

    return config


app = cdk.App()

config_sets = load_account_set_config("mlops_sm_project_template/config/accounts.json")

pipeline_env = cdk.Environment(account=PIPELINE_ACCOUNT, region=DEFAULT_DEPLOYMENT_REGION)

CodeCommitStack(app, "ml-sc-cc-repo", env=pipeline_env)

for config_set in config_sets:
    PipelineStack(app, f"ml-sc-deploy-pipeline-{config_set['SET_NAME']}", env=pipeline_env, config_set=config_set)

# Personal Stacks for testing locally, comment out when committing to repository
# if not os.getenv("CODEBUILD_BUILD_ARN"):
#     CoreStage(
#         app,
#         "Personal",  ## change this to another stack name when doing local tests
#         env=deployment_env,
#     )


app.synth()
