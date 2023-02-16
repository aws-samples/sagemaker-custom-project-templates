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

from aws_cdk import (
    Environment,
    Stack,
    Stage,
)

from constructs import Construct

from mlops_sm_project_template.service_catalog_stack import ServiceCatalogStack


class CoreStage(Stage):
    """
    Core Stage
    Core Stage which handles the creation of stacks that would be used to deploy key components service catalog product for mlops project template for sagemaker projects
    - ServiceCatalogStack: handles the creation of service catalog related resources and deploy product for sagemaker projects
    """

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:

        super().__init__(scope, id, **kwargs)

        service_catalog_stack = ServiceCatalogStack(self, "MLOpsServiceCatalog", **kwargs)
