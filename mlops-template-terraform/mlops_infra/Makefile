.DEFAULT_GOAL = help
.PHONY: help bootstrap init plan apply

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

bootstrap:
	@./scripts/terraform-account-setup.sh

init:
	@cd terraform && terraform init

plan:
	@cd terraform && terraform plan

apply:
	@cd terraform && terraform apply
