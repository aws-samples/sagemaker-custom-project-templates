# KMS

A module to create [AWS KMS Customer Managed Key](https://docs.aws.amazon.com/kms/latest/developerguide/concepts.html#customer-cmk) with cross account decrypt access to the preprod and prod accounts to get ML artifacts. 

<!-- BEGIN_AUTOMATED_TF_DOCS_BLOCK -->
## Requirements

No requirements.

## Usage
Basic usage of this module is as follows:
```hcl
module "example" {
	 source  = "<module-path>"

	 # Required variables
	 account_id  = 

	 # Optional variables
	 description  = "KMS Key for Machine Learning workloads."
	 trusted_accounts_for_decrypt_access  = []
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
| [aws_kms_key.key](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms_key) | resource |
| [aws_ssm_parameter.kms_key](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ssm_parameter) | resource |
| [aws_iam_policy_document.key_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_account_id"></a> [account\_id](#input\_account\_id) | AWS account ID | `string` | n/a | yes |
| <a name="input_description"></a> [description](#input\_description) | Description of KMS key | `string` | `"KMS Key for Machine Learning workloads."` | no |
| <a name="input_trusted_accounts_for_decrypt_access"></a> [trusted\_accounts\_for\_decrypt\_access](#input\_trusted\_accounts\_for\_decrypt\_access) | List of AWS account numbers that read ML artifacts from the bucket | `list(string)` | `[]` | no |
## Outputs

| Name | Description |
|------|-------------|
| <a name="output_key_arn"></a> [key\_arn](#output\_key\_arn) | n/a |
| <a name="output_key_id"></a> [key\_id](#output\_key\_id) | n/a |
<!-- END_AUTOMATED_TF_DOCS_BLOCK -->