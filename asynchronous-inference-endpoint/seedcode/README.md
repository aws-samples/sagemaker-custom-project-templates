# SageMaker Projects: Asynchronous Inference

Guide: 

1. Create a SM Project for deployment only
2. Clone locally the content of the deployment only code repository
3. Copy the content of this repository in the folder just created
4. Make sure that the assumed role `AmazonSageMakerServiceCatalogProductsUseRole` has the `SNS:CreateTopic` permissions
5. Provide the test file S3 path in the `staging-config.json` file
6. Push to CodeCommit