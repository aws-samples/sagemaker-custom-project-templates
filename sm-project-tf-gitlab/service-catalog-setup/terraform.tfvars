# Region Variable
region = "us-east-1"

# Environment definining Variables
env          = "dev"
organization = "machine-learning"
role         = "ops"

# Service Catalog Owners
sc_portfolio_owner = "Admin"
sc_product_owner   = "Admin"


# Service Catalog Launch Role
sc_product_launch_role = "CustomAmazonSagemakerServiceCatalogProductLaunchRole"

# Service Catalog Execution Role. Use the SageMaker Studio Execution Role
sc_portfolio_service_role = "role/service-role/<AmazonSageMakerExecRole>"

# Prefix for DynamoDB Table Name to store Backend TF State
backend_table_prefix = "terraform-tfstate-dev"

# Pass Role Variable for Command Runner to assume Service Catalog
cm_exec_pass_role_arn = "role/service-role/AmazonSageMakerServiceCatalog*"

# Command Runner Exec Role
command_runner_exec_role = "CommandRunnerExecRole"

#Gitlab Private Token
gitlab_private_token = ""

#Gitlab IAM Access Key
gitlab_iam_access_key = ""

#Gitlab IAM Secret Key
gitlab_iam_secret_key = ""