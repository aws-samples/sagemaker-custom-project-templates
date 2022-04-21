# Serverless Inference Endpoint Deployment Pipeline

## Purpose

Use this template to automate the entire model lifecycle that includes both model building and deployment workflows. Ideally suited for continuous integration and continuous deployment (CI/CD) of ML models. Process data, extract features, train and test models, and register them in the model registry. The template provisions an AWS CodeCommit repository for checking in and managing code versions. Kick off the model deployment workflow by approving the model registered in the model registry for deployment either manually or automatically. You can customize the seed code and the configuration files to suit your requirements. AWS CodePipeline is used to orchestrate the model deployment. Model building pipeline: SageMaker Pipelines Code repository: AWS CodeCommit Orchestration: AWS CodePipeline

This project is derived from the built-in [Build, Train, and Deploy Project](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-projects-templates-sm.html#sagemaker-projects-templates-code-commit) but uses serverless inference endpoints.

## Instructions

1. Run `sh init.sh <AWS-BUCKET>`
2. Create a Product in Service Catalog using the `template.yml` file as CFN and add the Product to the Portfolio
3. Set the `sagemaker:studio-visibility` tag to `true` in the Product
4. Launch in the SageMaker Projects Organization Templates page