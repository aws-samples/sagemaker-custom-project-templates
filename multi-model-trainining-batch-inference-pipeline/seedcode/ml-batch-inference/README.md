# SageMaker Projects: MLOps template for Batch Inference with Batch Transform and SageMaker Pipelines

Guide to use this template:

1. Create a "Deploy only" project in SageMaker Projects, specifying the Model Package Group Name that you want to use
2. Copy the content of this repository into the folder created by project
3. Change the `*-config.json` files to the input path and output path that you want to use for batch inference
4. Push the changes to CodeCommit from the SageMaker Studio IDE / your IDE of choice
5. Go to CodePipeline and check the pipeline related to the project.