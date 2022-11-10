# Region
region = "us-east-1"

# Variables to define Environment
env          = "mlops"
organization = "sagemaker"
role         = "pipelines"

# IAM Roles for Service Catalog and Pipeline resource executions. 
sagemaker_service_catalog_codebuild_role    = "role/service-role/AmazonSageMakerServiceCatalogProductsUseRole"
sagemaker_service_catalog_exec_role         = "role/service-role/AmazonSageMakerServiceCatalogProductsUseRole"
sagemaker_service_catalog_codepipeline_role = "role/service-role/AmazonSageMakerServiceCatalogProductsUseRole"
sagemaker_service_catalog_events_role       = "role/service-role/AmazonSageMakerServiceCatalogProductsEventsRole"
sagemaker_service_catalog_lambda_role       = "role/service-role/AmazonSageMakerServiceCatalogProductsUseRole"