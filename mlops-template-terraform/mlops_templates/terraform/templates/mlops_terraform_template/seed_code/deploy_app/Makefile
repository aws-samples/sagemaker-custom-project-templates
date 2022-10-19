
bootstrap:
	@sh infra_scripts/bootstrap.sh

init:
	@cd terraform && terraform init
    
get-latest-model:
	@python infra_scripts/get_last_approved_model.py

plan: get-latest-model
	@cd terraform && terraform plan

apply: get-latest-model
	@cd terraform && terraform apply
    
auto-apply: init get-latest-model plan
	@cd terraform && terraform apply -auto-approve
    
