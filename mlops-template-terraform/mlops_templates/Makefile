.DEFAULT_GOAL = help
.PHONY: help bootstrap init plan apply

bootstrap:
	@./scripts/terraform-account-setup.sh

init:
	@cd terraform/ && terraform init

plan:
	@cd terraform/ && terraform plan

apply:
	@cd terraform/ && terraform apply

destroy:
	@cd terraform/ && terraform destroy
