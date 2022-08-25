# Dynamic Account Project Template
This template mainly differs to the [Basic Project Template](BASIC_PROJECT_TEMPLATE.md) in the template parameters. The archietcture and other componenets are exactly the same. 

## Dynamic Project Stack
![project architecture](../../diagrams/MLOPs%20Foundation%20Architecture-sagemaker%20project%20architecture.jpg)

The stack expects 5 cloudformation parameters:
- **Project Name:** This parameter is of type `String` and is mandatory to be created for SageMaker Project. It will be visible in SageMaker Studio Domain and be used to then tag all the resources related to SageMaker and have them visible under the project tab. It must be named `SageMakerProjectName`.
- **Project ID:** This parameter is of type `String` and is mandatory to be created for SageMaker Project. When creating a project in SageMaker Studio Domain and it will be automatically generated and then used to tag all the resources related to SageMaker and have them visible under the project tab. It must be named `SageMakerProjectId`.


