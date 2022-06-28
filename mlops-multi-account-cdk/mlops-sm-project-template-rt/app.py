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
from mlops_sm_project_template_rt.pipeline_stack import PipelineStack, CoreStage
from mlops_sm_project_template_rt.codecommit_stack import CodeCommitStack
from mlops_sm_project_template_rt.config.constants import DEFAULT_DEPLOYMENT_REGION, PIPELINE_ACCOUNT, DEV_ACCOUNT

app = cdk.App()

pipeline_env = cdk.Environment(account=PIPELINE_ACCOUNT, region=DEFAULT_DEPLOYMENT_REGION)
deployment_env = cdk.Environment(account=DEV_ACCOUNT, region=DEFAULT_DEPLOYMENT_REGION)

CodeCommitStack(app, "ml-sg-cc-repo", env=pipeline_env)
PipelineStack(app, "ml-sg-deploy-pipeline", env=pipeline_env)

# Personal Stacks for testing locally, comment out when committing to repository
if not os.getenv("CODEBUILD_BUILD_ARN"):
    CoreStage(
        app,
        "Personal",  ## change this to another stack name when doing local tests
        env=deployment_env,
    )


app.synth()
