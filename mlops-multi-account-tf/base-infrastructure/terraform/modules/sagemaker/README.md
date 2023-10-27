# SageMaker

Module that creates a SagMaker Studio Domain, Studio users, and Service Catalog products for SageMaker Projects.

<!-- BEGIN_AUTOMATED_TF_DOCS_BLOCK -->
## Requirements

No requirements.

## Usage
Basic usage of this module is as follows:
```hcl
module "example" {
	 source  = "<module-path>"

	 # Required variables
	 data_scientist_execution_role_arn  = 
	 lead_data_scientist_execution_role_arn  = 
	 private_subnet_id  = 
	 private_subnet_id_2  = 
	 sg_id  = 
	 sm_studio_role_arn  = 
	 vpc_id  = 

	 # Optional variables
	 studio_domain_name  = "studio-domain"
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
| [aws_sagemaker_domain.sagemaker_domain](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sagemaker_domain) | resource |
| [aws_sagemaker_servicecatalog_portfolio_status.enable_sagemaker_servicecatalog_portfolio](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sagemaker_servicecatalog_portfolio_status) | resource |
| [aws_sagemaker_user_profile.data_scientist_sagemaker_user_profiles](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sagemaker_user_profile) | resource |
| [aws_sagemaker_user_profile.lead_data_scientist_sagemaker_user_profiles](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sagemaker_user_profile) | resource |
## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_data_scientist_execution_role_arn"></a> [data\_scientist\_execution\_role\_arn](#input\_data\_scientist\_execution\_role\_arn) | Data Scientist role ARN | `string` | n/a | yes |
| <a name="input_lead_data_scientist_execution_role_arn"></a> [lead\_data\_scientist\_execution\_role\_arn](#input\_lead\_data\_scientist\_execution\_role\_arn) | Lead Data Scientist role ARN | `string` | n/a | yes |
| <a name="input_private_subnet_id"></a> [private\_subnet\_id](#input\_private\_subnet\_id) | Private subnet id | `string` | n/a | yes |
| <a name="input_private_subnet_id_2"></a> [private\_subnet\_id\_2](#input\_private\_subnet\_id\_2) | Private subnet id | `string` | n/a | yes |
| <a name="input_sg_id"></a> [sg\_id](#input\_sg\_id) | Security group id | `string` | n/a | yes |
| <a name="input_sm_studio_role_arn"></a> [sm\_studio\_role\_arn](#input\_sm\_studio\_role\_arn) | SageMaker Studio ARN | `string` | n/a | yes |
| <a name="input_studio_domain_name"></a> [studio\_domain\_name](#input\_studio\_domain\_name) | Name to assign to the SageMaker Studio domain | `string` | `"studio-domain"` | no |
| <a name="input_vpc_id"></a> [vpc\_id](#input\_vpc\_id) | VPC ID where to deploy SageMaker Studio | `string` | n/a | yes |
## Outputs

No outputs.
<!-- END_AUTOMATED_TF_DOCS_BLOCK -->