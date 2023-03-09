# SageMaker Build - Train Pipelines

This folder contains all the SageMaker Pipelines of your project.

`.github/workflows/build_sagemaker_pipeline.yml` defines how to run a pipeline after each commit to this repository.
`ml_pipelines/` contains the SageMaker pipelines definitions.
The expected output of the your main pipeline (here `training/pipeline.py`) is a model registered to SageMaker Model Registry.

`source_scripts/` contains the underlying scripts run by the steps of your SageMaker Pipelines. For example, if your SageMaker Pipeline runs a Processing Job as part of a Processing Step, the code being run inside the Processing Job should be defined in this folder.
A typical folder structure for `source_scripts/` can contain `helpers`, `preprocessing`, `training`, `postprocessing`, `evaluate`, depending on the nature of the steps run as part of the SageMaker Pipeline.
We provide here an example with the Abalone dataset, to train an XGBoost model (using), and exaluating the model on a test set before sending it for manual approval to SageMaker Model Registry inside the SageMaker ModelPackageGroup defined when creating the SageMaker Project.
Additionally, if you use custom containers, the Dockerfile definitions should be found in that folder.

`tests/` contains the unittests for your `source_scripts/`

`notebooks/` contains experimentation notebooks.

# Run pipeline from command line from this folder

```
pip install -e .

run-pipeline --module-name ml_pipelines.training.pipeline \
          --role-arn {SAGEMAKER_PIPELINE_ROLE_ARN} \
          --kwargs "{\"region\":\"{AWS_REGION}\",\"role\":\"{SAGEMAKER_PIPELINE_ROLE_ARN}\",\"default_bucket\":\"{ARTIFACT_BUCKET}\",\"pipeline_name\":\"${SAGEMAKER_PROJECT_NAME}-${SAGEMAKER_PROJECT_ID}\",\"model_package_group_name\":\"{MODEL_PACKAGE_GROUP_NAME}\",\"base_job_prefix\":\"MLOPS\", \"bucket_kms_id\":\"{ARTIFACT_BUCKET_KMS_ID}\"}"'
```
