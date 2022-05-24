import importlib
from aws_cdk import (
    Fn,
    aws_ec2 as ec2,
)

from constructs import Construct

"""
This is an optional construct to setup the Networking resources (VPC and Subnets) from existing resources in the account to be used in the CDK APP.
"""
class Networking(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        stage_name: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # load constants required for each stage
        try:
            stage_constants = importlib.import_module(f"mlops_infra.config.{stage_name}.constants")
        except Exception:
            stage_constants = importlib.import_module(
                "mlops_infra.config.dev.constants"
            )  # use default configs which are inf-dev configs in this case

        # vpc resource to be used for the endpoint and lambda vpc configs
        self.vpc = ec2.Vpc.from_vpc_attributes(self, "VPC", vpc_id=stage_constants.VPC_ID, availability_zones=Fn.get_azs())

        # subnets resources should use
        self.subnets = [
            ec2.Subnet.from_subnet_id(self, f"SUBNET-{subnet_id}", subnet_id)
            for subnet_id in stage_constants.APP_SUBNETS
        ]