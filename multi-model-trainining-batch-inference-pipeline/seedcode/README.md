# SageMaker Projects: MLOps template for Multi-model training and batch inference pipeline

Guide to use this template:

1. Create a "multi-model-train-template" project in SageMaker Projects, specifying the Model Package Group Name that you want to use
2. Clone the two git repositories
3. Copy the content of [ml-build-train](./ml-build-train/) in your repository for training
4. Copy the content of [ml-batch-inference](./ml-batch-inference/) in your repository for batch inference
5. Change the `*-config.json` files to the input path and output path that you want to use for batch inference
6. Push the changes to CodeCommit from the SageMaker Studio IDE / your IDE of choice
7. Go to CodePipeline and check the pipeline related to the project.