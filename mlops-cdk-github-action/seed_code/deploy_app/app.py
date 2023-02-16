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

from deploy_endpoint.deploy_endpoint_stack import DeployEndpointStack
from config.constants import (
    DEFAULT_DEPLOYMENT_REGION,
    DEV_ACCOUNT,
    PROJECT_ID,
    PROJECT_NAME
)
import aws_cdk as cdk

app = cdk.App()

dev_env = cdk.Environment(account=DEV_ACCOUNT, region=DEFAULT_DEPLOYMENT_REGION)

DeployEndpointStack(app, f"dev-{PROJECT_NAME}-{PROJECT_ID}", env=dev_env)

app.synth()
