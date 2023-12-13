# Service catalog for SageMaker Projects

A re-usable module that simplifies adding and maintaining service catalog products for SageMaker Products.

This module supports taking a number of named templates. The templates are expected to be in a folder called `sagemaker_templates`. For example, if you you have your service catalog templates saves as such:

```
├── main.tf
├── sagemaker_templates
│   ├── sagemaker_project_train.yaml
│   ├── sagemaker_project_train_and_deploy.yaml
│   └── sagemaker_project_workflow.yaml
└── *.tf
```

Then you can define service catalog template in your `main.tf` as such.

```hcl
module "service_catalog" {
  source  = "<module-path>"
  ...
  templates = {
    template1 = {
      name : "MLOps template for model building, training, and deployment",
      file : "sagemaker_project_train_and_deploy",
      description : "Use this template to automate the entire model lifecycle that includes both model building and deployment workflows. Suited for continuous integration and continuous deployment (CI/CD) of ML models. Process data, extract features, train and test models, and register them in the model registry. The template provisions a GitHub repository for checking in and managing code versions. Kick off the model deployment workflow by approving the model registered in the model registry for deployment either manually or automatically. You can customize the seed code and the configuration files to suit your requirements. GitHub Actions is used to orchestrate the model deployment. Model building pipeline: SageMaker Pipelines Code repository and Orchestration: GitHub (<Your> organisation)"
    },
    template2 = {
      name : "MLOps template for model building and training",
      file : "sagemaker_project_train",
      description : "Use this template to automate the entire model lifecycle that includes both model building and deployment workflows. Suited for continuous integration and continuous deployment (CI/CD) of ML models. Process data, extract features, train and test models, and register them in the model registry. The template provisions a GitHub repository for checking in and managing code versions. Kick off the model deployment workflow by approving the model registered in the model registry for deployment either manually or automatically. You can customize the seed code and the configuration files to suit your requirements. GitHub Actions is used to orchestrate the model deployment. Model building pipeline: SageMaker Pipelines Code repository and Orchestration: GitHub (<Your> organisation)"
    },
    template3 = {
      name : "MLOps template for workflow promotion",
      file : "sagemaker_project_workflow",
      description : "Use this template to automate the model building workflow. Process data, extract features, train and test models, and register them in the model registry. The template provisions a GitHub repository for checking in and managing code versions. You can customize the seed code and the configuration files to suit your requirements."
    }
  }

}
```

**Adding new projects or updating existing projects**

Typically, you require two artifacts for a SageMaker project:
1. A CloudFormation template for service catalog.
2. One or more Git Repositories (as templates) that your cloudformation template clones.

We recommend you get started with an existing project cloudformation template and customize it as per your need.

Our templates use custom cloudformtion resources (Lambda functions) that make API calls to GitHub to:
- Clone private repo from a template repo
- Trigger a GitHub Action Workflow when a new model is registered

The lambdas used here are deployed in the dev account. You can review them at `terraform/dev/lambdas/`.


<!-- BEGIN_AUTOMATED_TF_DOCS_BLOCK -->
## Requirements

No requirements.

## Usage
Basic usage of this module is as follows:
```hcl
module "example" {
	 source  = "<module-path>"

	 # Required variables
	 bucket_domain_name  = 
	 bucket_id  = 
	 environment  = 
	 launch_role  = 
	 lead_data_scientist_execution_role_arn  = 
	 templates  = 
}
```
## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | n/a |
## Modules

No modules.
## Resources

| Name | Type |
|------|------|
| [aws_s3_object.template_object](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_object) | resource |
| [aws_servicecatalog_constraint.constraint](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/servicecatalog_constraint) | resource |
| [aws_servicecatalog_portfolio.sagemaker_portfolio](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/servicecatalog_portfolio) | resource |
| [aws_servicecatalog_principal_portfolio_association.sagemaker](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/servicecatalog_principal_portfolio_association) | resource |
| [aws_servicecatalog_product.product](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/servicecatalog_product) | resource |
| [aws_servicecatalog_product_portfolio_association.sagemaker_product_to_portfolio](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/servicecatalog_product_portfolio_association) | resource |
| [aws_servicecatalog_provisioning_artifact.artifact](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/servicecatalog_provisioning_artifact) | resource |
## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_bucket_domain_name"></a> [bucket\_domain\_name](#input\_bucket\_domain\_name) | The AWS region this bucket resides in | `string` | n/a | yes |
| <a name="input_bucket_id"></a> [bucket\_id](#input\_bucket\_id) | Bucket ID with Sagemaker Templates | `string` | n/a | yes |
| <a name="input_environment"></a> [environment](#input\_environment) | Environment | `string` | n/a | yes |
| <a name="input_launch_role"></a> [launch\_role](#input\_launch\_role) | Launch Role ARN | `string` | n/a | yes |
| <a name="input_lead_data_scientist_execution_role_arn"></a> [lead\_data\_scientist\_execution\_role\_arn](#input\_lead\_data\_scientist\_execution\_role\_arn) | Lead Data Scientist role ARN | `string` | n/a | yes |
| <a name="input_templates"></a> [templates](#input\_templates) | List of template files | `list(string)` | n/a | yes |
## Outputs

No outputs.
<!-- END_AUTOMATED_TF_DOCS_BLOCK -->