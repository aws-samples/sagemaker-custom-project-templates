# Developer Guide
While the solution presented in [README](README.md) can be used as is, this repository is built with the intention to be customized for the need of your organization.

[mlops-infra](mlops-infra/) will:
- Create or import VPCs via [networking_stack](mlops_infra/networking_stack.py). If created, the stack will create the required VPC endpoint for SageMaker studio and for deploying SageMaker endpoints and pipelines. If imported, ensure that the VPC you import contains at least the VPC endpoints listed in [README](README.md)
- Create networking SSM parameters via [networking_stack](mlops_infra/networking_stack.py) that will be used in the respective account either to deploy SageMaker studio or to deploy SageMaker endpoints.
- Create a SageMaker studio domain via [sagemaker_studio_stack](mlops_infra/sagemaker_studio_stack.py) alongside SageMaker studio users and the required roles. The list of roles and policies is defined in [sm_roles](mlops_infra/constructs/sm_roles.py)

This means for example that:
If you want to modify the policies associated with your SageMaker studio users (what a user can do from SageMaker studio in the account), you should modify [sm_roles](mlops_infra/constructs/sm_roles.py).

If you would like to give data scientists access to EMR for exploration from SageMaker Studio, you would modify the policy in the following way: (repeat the operation lead data scientists a few lines below)

```
        # role for Data Scientist persona
        self.data_scientist_role = iam.Role(
            self,
            "data-scientist-role",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("lambda.amazonaws.com"),
                iam.ServicePrincipal("sagemaker.amazonaws.com"),
            ),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMReadOnlyAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSLambda_ReadOnlyAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSCodeCommitReadOnly"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryReadOnly"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEMRFullAccessPolicy_v2"),    <--- Added EMR Managed Policy
            ],
        )
```

Similarly:
If you want to enable SageMaker Studio inside the VPC to communicate with Glue, in [networking_stack](networking_stack.py) you would add:

```
        # GLUE VPC Endpoint
        self.primary_vpc.add_interface_endpoint("GLUEEndpoint", service=ec2.InterfaceVpcEndpointAwsService.GLUE)
```