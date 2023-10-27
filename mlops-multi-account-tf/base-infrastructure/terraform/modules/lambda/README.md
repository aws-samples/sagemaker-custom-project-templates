# Lamda

Generic module to create AWS Lambda functions. For MLOps, AWS Lambda functions are deployed to make GitHub API calls.

<!-- BEGIN_AUTOMATED_TF_DOCS_BLOCK -->
## Requirements

No requirements.

## Usage
Basic usage of this module is as follows:
```hcl
module "example" {
	 source  = "<module-path>"

	 # Required variables
	 description  = 
	 filename  = 
	 function_name  = 
	 handler  = 
	 layers  = 
	 reserved_concurrent_executions  = 
	 role  = 
	 runtime  = 
	 security_groups  = 
	 source_code_hash  = 
	 subnets_ids  = 
	 timeout  = 
	 variables  = 
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
| [aws_cloudwatch_log_group.log_group](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group) | resource |
| [aws_lambda_function.lambda](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function) | resource |
## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_description"></a> [description](#input\_description) | n/a | `any` | n/a | yes |
| <a name="input_filename"></a> [filename](#input\_filename) | n/a | `any` | n/a | yes |
| <a name="input_function_name"></a> [function\_name](#input\_function\_name) | n/a | `any` | n/a | yes |
| <a name="input_handler"></a> [handler](#input\_handler) | n/a | `any` | n/a | yes |
| <a name="input_layers"></a> [layers](#input\_layers) | n/a | `any` | n/a | yes |
| <a name="input_reserved_concurrent_executions"></a> [reserved\_concurrent\_executions](#input\_reserved\_concurrent\_executions) | n/a | `any` | n/a | yes |
| <a name="input_role"></a> [role](#input\_role) | n/a | `any` | n/a | yes |
| <a name="input_runtime"></a> [runtime](#input\_runtime) | n/a | `any` | n/a | yes |
| <a name="input_security_groups"></a> [security\_groups](#input\_security\_groups) | n/a | `any` | n/a | yes |
| <a name="input_source_code_hash"></a> [source\_code\_hash](#input\_source\_code\_hash) | n/a | `any` | n/a | yes |
| <a name="input_subnets_ids"></a> [subnets\_ids](#input\_subnets\_ids) | n/a | `any` | n/a | yes |
| <a name="input_timeout"></a> [timeout](#input\_timeout) | n/a | `any` | n/a | yes |
| <a name="input_variables"></a> [variables](#input\_variables) | n/a | `any` | n/a | yes |
## Outputs

| Name | Description |
|------|-------------|
| <a name="output_lambda_arn"></a> [lambda\_arn](#output\_lambda\_arn) | The arn of the Lambda function |
| <a name="output_lambda_name"></a> [lambda\_name](#output\_lambda\_name) | The name of the Lambda function |
| <a name="output_log_arn"></a> [log\_arn](#output\_log\_arn) | The Cloudwatch log group arn |
| <a name="output_log_name"></a> [log\_name](#output\_log\_name) | The Cloudwatch log group name |
<!-- END_AUTOMATED_TF_DOCS_BLOCK -->