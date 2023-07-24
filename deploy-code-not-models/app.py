#!/usr/bin/env python3
import os

import aws_cdk as cdk

from deploy_code_not_models.tooling_account_stack import ToolingAccountResources
from deploy_code_not_models.deployment_accounts_stack import DeploymentAccountResources
from deploy_code_not_models.config.constants import constants


app = cdk.App()

ToolingAccountResources(
    app,
    "ToolingAccountResources",
    env=cdk.Environment(account=constants["dev"], region=constants["region"]),
    dev_account=constants["dev"],
    stg_account=constants["stg"],
    prod_account=constants["prod"],
    project_name=constants["project_name"],
    project_id=constants["project_id"],
)
DeploymentAccountResources(
    app,
    "PreProdAccountResources",
    env=cdk.Environment(account=constants["stg"], region=constants["region"]),
    tooling_account=constants["dev"],
    project_name=constants["project_name"],
    project_id=constants["project_id"],
)
DeploymentAccountResources(
    app,
    "ProdAccountResources",
    env=cdk.Environment(account=constants["prod"], region=constants["region"]),
    tooling_account=constants["dev"],
    project_name=constants["project_name"],
    project_id=constants["project_id"],
)

app.synth()
