from aws_cdk import Aws, Stack, Tags
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_kms as kms
from aws_cdk import aws_ssm as ssm
from constructs import Construct

from config.constants import (
    PROJECT_ID,
    PROJECT_NAME,
)
from deploy_sagemaker_pipeline.deploy_sm_pipeline import DeploySMPipelineConstruct

class BackendStack(Stack):
    """
    This example BackendStack class currently creates:
    - a SageMaker pipeline to run a SageMaker Batch Transform job (or more)
    - If needed imports a VPC which can be reused for any infrastructure (currently None)
    """
    def import_vpc(self) -> ec2.Vpc:
        """Imports the VPC into this stack

        Returns:
            ec2.Vpc: the VPC
        """
        vpc_id = ssm.StringParameter.value_from_lookup(self, "/vpc/id")
        return ec2.Vpc.from_lookup(self, "VPC", vpc_id=vpc_id)


    def __init__(
        self,
        scope: Construct,
        id: str,
        **kwargs,
    ):

        super().__init__(scope, id, **kwargs)

        Tags.of(self).add("sagemaker:project-id", PROJECT_ID)
        Tags.of(self).add("sagemaker:project-name", PROJECT_NAME)
        Tags.of(self).add("sagemaker:deployment-stage", Stack.of(self).stack_name)

        # SM Pipeline backend construct
        sm_pipeline = DeploySMPipelineConstruct(self, "smpipeline")
