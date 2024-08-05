# Amazon SageMaker Projects with Terraform Cloud

This section of the repository contains steps to set up custom Amazon SageMaker Project templates using Terraform Cloud without the use of AWS CloudFormation.

[A SageMaker Project](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-projects-whatis.html) leverages [AWS Service Catalog](https://docs.aws.amazon.com/servicecatalog/latest/adminguide/introduction.html) to manage and provision the Infrastructure-as-Code that underly a SageMaker Project template. This allows organizations to standardize and automate the deployment of infraustructre necessary in a Machine Learning Model Lifecycle. 

Most available patterns for SageMaker Project custom templates require the use of AWS CloudFormation at some capactiy. However, for many enteperise Amazon SageMaker customers, vendor-specific IaC is strictly prohibited, blocking customers from leveraging custom SageMaker Project templates. With this solution, organizations can use Terraform Cloud to manage and deploy custom SageMaker Projects templates strictly within Terraform Cloud without the use of AWS CloudFormation.


## Service Catalog Engine for Terraform Cloud

Under the hood, SageMaker Projects are managed and provisioned by AWS Service Catalog with each SageMaker Project mapped directly to a product in a Service Catalog portfolio. The [Service Catalog Engine (SCE) for Terraform Cloud](https://github.com/hashicorp/aws-service-catalog-engine-for-tfc), maintained by Hashicorp, is a Terraform module that deploys AWS-native infraustructure to manage direct integration between AWS Service Catalog and Terraform Cloud. With the SCE, along with customizations contained in this template, organizations can use Terraform Cloud to manage and deploy SageMaker Projects without the use of AWS CloudFormation.

## Prerequisites
To successfully deploy the example, you must have the following:
1. An AWS Account with the necessary permissions to create and manage SageMaker Projects and Service Catalog products. Refer to the [Service Catalog documentation](https://docs.aws.amazon.com/servicecatalog/latest/adminguide/introduction.html) for more information on Service Catalog permissions.
2. An existing SageMaker Studio Domain with an associated SageMaker User Profile. The SageMaker Studio Domain *must* have SageMaker Projects enabled. Refer to [the SageMaker documentation](https://docs.aws.amazon.com/sagemaker/latest/dg/onboard-quick-start.html) for performing a "quick setup" of a SageMaker Studio domain.
3. An existing Terraform Cloud account with the necessary permissions to create and manage workspaces. Refer to [Terraform teams and organizations documentation](https://www.terraform.io/docs/cloud/users-teams-organizations/permissions.html) for more information on Terraform Cloud permissions.
4. A Unix terminal with the `aws-cli` and `terraform` installed. Refer to the [AWS CLI documentation](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) and the [Terraform documentation](https://learn.hashicorp.com/tutorials/terraform/install-cli) for more information on installation.

## Getting Started
1. Clone this repository to your local machine, update the submodules, and navigate to the `mlops-terraform-cloud` directory
```
$ git clone https://github.com/aws-samples/sagemaker-custom-project-templates.git
$ git submodule update --init --recursive
$ cd sagemaker-custom-project-templates/mlops-terraform-cloud
```

2. Login to your Terraform Cloud account
```
$ terraform login
```

3. Navigate to your AWS Account and retrieve the SageMaker User Role ARN for the SageMaker User Profile associated with your SageMaker Studio Domain. This role is used to grant SageMaker Studio users permissions to create and manage SageMaker Projects. The role ARN should look like `arn:aws:iam::012345678910:role/service-role/AmazonSageMaker-ExecutionRole`

4. Create a tfvars file with the necessary variables for the Terraform Cloud workspace 
```
cp terraform.tfvars.example terraform.tfvars
```

5. Set the appropriate values in the newly created `terraform.tfvars` file. The following variables are required:
```
tfc_organization = "my-tfc-organization"
tfc_team = "aws-service-catalog"
token_rotation_interval_in_days = 30
sagemaker_user_role_arns        = ["arn:aws:iam::012345678910:role/service-role/AmazonSageMaker-ExecutionRole"]
```

6. Initialize the Terraform Cloud workspace
```
$ terraform init
```

7. Apply the Terraform Cloud workspace
```
terraform apply
```
8. Navigate back to the SageMaker Console and open the SageMaker Studio application through the user profile assoicated with the SageMaker User Role ARN provided

9. Within SageMaker Studio's left-hand tool bar, under "Deployments" select "Projects"

10. Click "Create project", select the `mlops-tf-cloud-example` product under "Organization templates", and then select "Next"

11. Parameterize the template with a unique name and optionally give a project description, then click "Create"

12. In a separate tab or window, navigate back to your Terraform Cloud account's Workspaces, and you'll see a workspace being provisioned directly from your SageMaker Project deployment. The naming convention of the Workspace will be `<ACCOUNT_ID>-<SAGEMAKER_PROJECT_ID>`

## Further Customization
This example can be simply modified to include custom Terraform to be included in your SageMaker Project template. To do so, simply navigate to the `mlops-product` sub-directory and define your SageMaker Project template in Terraform. When ready to deploy, be sure to archive and compress this Terraform using the following

```
cd mlops-product
tar -czf product.tar.gz product
```
