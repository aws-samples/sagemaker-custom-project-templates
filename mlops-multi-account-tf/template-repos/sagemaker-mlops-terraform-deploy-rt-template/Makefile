SHELL := /usr/bin/env bash

.PHONY: tf-plan
tf-plan: 
	terraform init \
	-backend-config="bucket=${bucket}" \
	-backend-config="region=${region}" \
	-backend-config="key=${key}" \
	-backend-config="dynamodb_table=${table}" \
	-backend-config="encrypt=true" \
	-reconfigure && \
	terraform validate && \
	terraform plan \
	-var region=${region} \
	-var-file ${var_file}
.PHONY: tf-apply
tf-apply:
	terraform init \
	-backend-config="bucket=${bucket}" \
	-backend-config="region=${region}" \
	-backend-config="key=${key}" \
	-backend-config="dynamodb_table=${table}" \
	-backend-config="encrypt=true" \
	-reconfigure && \
	terraform validate && \
	terraform apply \
	-var region=${region} \
	-var-file ${var_file} -auto-approve
.PHONY: tf-destroy
tf-destroy:
	terraform init \
	-backend-config="bucket=${bucket}" \
	-backend-config="region=${region}" \
	-backend-config="key=${key}" \
	-backend-config="dynamodb_table=${table}" \
	-backend-config="encrypt=true" \
	-reconfigure && \
	terraform destroy \
	-var region=${region} \
	-var-file ${var_file} \
	-auto-approve

