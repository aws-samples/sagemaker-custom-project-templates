# MLOps offering SageMaker Project

This folder contains the CDK stacks that define the SageMaker project available in Service Catalog and deployable by Data Scientists & Machine Learning Engineers through SageMaker Studio.

The SageMaker Project creates two stacks whose definitions are controlled by `pipeline_stack` and can be found under the `constructs` folder:
- A "Build" stack that contains the model training and build pipeline. It creates a Code Pipeline in the Dev account, linked to the `build_app` Code Commit repository.
- A "Deploy" stack that contains the pipelines to deploy the models created and registered to SageMaker Model Registry through the "Build" pipeline in the Dev account. It creates 3 Code Pipelines in the Dev, QA and Prod accounts. Whenever a model is pushed to Model Registry, the "Deploy" Code Pipeline is triggered and deploys the content of the `deploy_app` Code Commit repository. It then tests the deployed model in Dev before promoting it to QA and requires manual approval from a lead Machine Learning Engineer or DevOps engineer before being promoted to Prod.

The folders `build_app/` and `deploy_app/` folders are the seed repositories that will populate Code Commit repositories of the same name, and whose content will be directly visible in SageMaker Studio once launching the SageMaker Project. Those can be cloned directly inside a SageMaker Studio environment.

Only the content of these folders are visible to Data Scientists, enabling them to freely modify their desired Machine Learning workflows through SageMaker pipelines, as well as integration tests for their models, inside SageMaker Studio. On the opposite, the Code Pipelines that controls the CICD workflows are abstracted away from Data Scientists and designed to stay in control of DevOps engineers.
