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


# This script is the main script of the cdk application. It controls which stacks are created when running cdk synth or cdk deploy in the repository
# In particular, this script is responsible for creating the "BackendStack" for the dev, preprod and prod environment. Through cdk synth it will accordingly generate 3 CloudFormation templates (in cdk.out/)

from backend_stack import BackendStack
from config.constants import (
    DEFAULT_DEPLOYMENT_REGION,
    DEV_ACCOUNT,
    PREPROD_ACCOUNT,
    PREPROD_REGION,
    PROD_ACCOUNT,
    PROD_REGION,
)
import aws_cdk as cdk

app = cdk.App()

dev_env = cdk.Environment(account=DEV_ACCOUNT, region=DEFAULT_DEPLOYMENT_REGION)
preprod_env = cdk.Environment(account=PREPROD_ACCOUNT, region=PREPROD_REGION)
prod_env = cdk.Environment(account=PROD_ACCOUNT, region=PROD_REGION)

BackendStack(app, "dev", env=dev_env)
BackendStack(app, "preprod", env=preprod_env)
BackendStack(app, "prod", env=prod_env)

app.synth()
