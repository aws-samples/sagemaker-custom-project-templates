# S3

Module to create AWS S3 buckets with versioning, tiering, and encryption.

<!-- BEGIN_AUTOMATED_TF_DOCS_BLOCK -->
## Requirements

No requirements.

## Usage
Basic usage of this module is as follows:
```hcl
module "example" {
	 source  = "<module-path>"

	 # Required variables
	 s3_bucket_force_destroy  = 
	 s3_bucket_name  = 
	 s3_bucket_policy  = 

	 # Optional variables
	 abort_incomplete_upload  = 1
	 cfn_file_name  = ""
	 days_to_intellegent_tiering  = 30
	 kms_key_id  = ""
	 mfa_delete  = "Disabled"
	 non_current_days_to_expire  = 360
	 non_current_days_to_glacier  = 90
	 non_current_days_to_standard_ia  = 30
	 object_source  = ""
	 sse_algorithm  = "aws:kms"
	 versioning  = "Disabled"
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
| [aws_s3_bucket.bucket](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket) | resource |
| [aws_s3_bucket_lifecycle_configuration.artifacts_lifecycle](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_lifecycle_configuration) | resource |
| [aws_s3_bucket_policy.bucket](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_policy) | resource |
| [aws_s3_bucket_public_access_block.bucket](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_public_access_block) | resource |
| [aws_s3_bucket_server_side_encryption_configuration.bucket](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_server_side_encryption_configuration) | resource |
| [aws_s3_bucket_versioning.bucket](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_versioning) | resource |
## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_abort_incomplete_upload"></a> [abort\_incomplete\_upload](#input\_abort\_incomplete\_upload) | Number of days until abort incomplete upload | `number` | `1` | no |
| <a name="input_cfn_file_name"></a> [cfn\_file\_name](#input\_cfn\_file\_name) | The name of s3 key. | `string` | `""` | no |
| <a name="input_days_to_intellegent_tiering"></a> [days\_to\_intellegent\_tiering](#input\_days\_to\_intellegent\_tiering) | Number of days to transition object to INTELLEGENT\_TIERING. | `number` | `30` | no |
| <a name="input_kms_key_id"></a> [kms\_key\_id](#input\_kms\_key\_id) | n/a | `string` | `""` | no |
| <a name="input_mfa_delete"></a> [mfa\_delete](#input\_mfa\_delete) | To enable/disable MFA delete | `string` | `"Disabled"` | no |
| <a name="input_non_current_days_to_expire"></a> [non\_current\_days\_to\_expire](#input\_non\_current\_days\_to\_expire) | Number of days to expire NON CURRENT objects. | `number` | `360` | no |
| <a name="input_non_current_days_to_glacier"></a> [non\_current\_days\_to\_glacier](#input\_non\_current\_days\_to\_glacier) | Number of days to transition NON CURRENT object to GLACIER. | `number` | `90` | no |
| <a name="input_non_current_days_to_standard_ia"></a> [non\_current\_days\_to\_standard\_ia](#input\_non\_current\_days\_to\_standard\_ia) | Number of days to transition NON CURRENT object to STANDARD\_IA. | `number` | `30` | no |
| <a name="input_object_source"></a> [object\_source](#input\_object\_source) | The location of objects to be added to s3 | `string` | `""` | no |
| <a name="input_s3_bucket_force_destroy"></a> [s3\_bucket\_force\_destroy](#input\_s3\_bucket\_force\_destroy) | String Boolean to set bucket to be undeletable (well more difficult anyway) e.g: true/false | `string` | n/a | yes |
| <a name="input_s3_bucket_name"></a> [s3\_bucket\_name](#input\_s3\_bucket\_name) | The name of the bucket | `string` | n/a | yes |
| <a name="input_s3_bucket_policy"></a> [s3\_bucket\_policy](#input\_s3\_bucket\_policy) | n/a | `any` | n/a | yes |
| <a name="input_sse_algorithm"></a> [sse\_algorithm](#input\_sse\_algorithm) | The type of encryption algorithm to use | `string` | `"aws:kms"` | no |
| <a name="input_versioning"></a> [versioning](#input\_versioning) | To enable/disable Versioning | `string` | `"Disabled"` | no |
## Outputs

| Name | Description |
|------|-------------|
| <a name="output_bucket_arn"></a> [bucket\_arn](#output\_bucket\_arn) | The ARN of the bucket. Will be of format arn:aws:s3:::bucketname. |
| <a name="output_bucket_id"></a> [bucket\_id](#output\_bucket\_id) | The name of the bucket. |
| <a name="output_s3_bucket_domain_name"></a> [s3\_bucket\_domain\_name](#output\_s3\_bucket\_domain\_name) | The AWS region this bucket resides in. |
| <a name="output_s3_bucket_region"></a> [s3\_bucket\_region](#output\_s3\_bucket\_region) | The AWS region this bucket resides in. |
<!-- END_AUTOMATED_TF_DOCS_BLOCK -->