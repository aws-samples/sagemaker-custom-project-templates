# sagemaker_inference_endpoint

<!-- BEGINNING OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.0 , < 1.1 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | ~> 3.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | ~> 3.0 |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_module_tags"></a> [module\_tags](#module\_module\_tags) | ../tags_module | n/a |

## Resources

| Name | Type |
|------|------|
| [aws_sagemaker_endpoint.inference_endpoint](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sagemaker_endpoint) | resource |
| [aws_sagemaker_endpoint_configuration.inference_endpoint_configuration](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sagemaker_endpoint_configuration) | resource |
| [aws_caller_identity.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/caller_identity) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_bucket_name"></a> [bucket\_name](#input\_bucket\_name) | The name of the S3 bucket. | `string` | n/a | yes |
| <a name="input_capture_modes"></a> [capture\_modes](#input\_capture\_modes) | Data Capture Mode. Acceptable Values Input and Output. | `list(string)` | <pre>[<br>  "Input",<br>  "Output"<br>]</pre> | no |
| <a name="input_csv_content_types"></a> [csv\_content\_types](#input\_csv\_content\_types) | The CSV content type headers to capture. | `list(string)` | <pre>[<br>  "text/csv"<br>]</pre> | no |
| <a name="input_enable_data_capture_config"></a> [enable\_data\_capture\_config](#input\_enable\_data\_capture\_config) | Enable Data Capture Config. | `bool` | `false` | no |
| <a name="input_initial_instance_count"></a> [initial\_instance\_count](#input\_initial\_instance\_count) | Instance Count. | `number` | `1` | no |
| <a name="input_initial_sampling_percentage"></a> [initial\_sampling\_percentage](#input\_initial\_sampling\_percentage) | Sampling Percentage.Acceptable Value Range Between 0 and 100. | `number` | `30` | no |
| <a name="input_initial_variant_weight"></a> [initial\_variant\_weight](#input\_initial\_variant\_weight) | Initial Variant Weight. Acceptable Value Range Between 0 and 1. | `number` | `1` | no |
| <a name="input_instance_type"></a> [instance\_type](#input\_instance\_type) | Instance Type. | `string` | `"ml.t2.medium"` | no |
| <a name="input_kms_key_arn"></a> [kms\_key\_arn](#input\_kms\_key\_arn) | KMS key ARN. | `string` | n/a | yes |
| <a name="input_model_name"></a> [model\_name](#input\_model\_name) | Approved Model Name. | `string` | n/a | yes |
| <a name="input_sagemaker_endpoint_configuration_name"></a> [sagemaker\_endpoint\_configuration\_name](#input\_sagemaker\_endpoint\_configuration\_name) | The name of the inference endpoint configuration. | `string` | n/a | yes |
| <a name="input_sagemaker_endpoint_name"></a> [sagemaker\_endpoint\_name](#input\_sagemaker\_endpoint\_name) | The name of the inference endpoint. | `string` | n/a | yes |
| <a name="input_tags"></a> [tags](#input\_tags) | Tags to be attached to the module tags of the resources. | `map(string)` | `{}` | no |
| <a name="input_variant_name"></a> [variant\_name](#input\_variant\_name) | The name of the variant. | `string` | `"variant-1"` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_inference_endpoint"></a> [inference\_endpoint](#output\_inference\_endpoint) | n/a |
<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
