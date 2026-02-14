# Terraform Build App

After a new project has been created and bootstrapped, you can update your SageMaker Pipelines and scripts that are
running in the different steps. The main files and folders to consider are:
- `/ml_pipelines` for adapting any necessary changes to the SageMaker Pipeline definition such as data sources, instance types
 and similiar
- `/source_scripts` for changing any of the source code for preprocessing, model evaluation or modelling logic.

In order for your changes to become effective and retrain the ML model with the new source code, you will need to push the
code to the repository:
- `$ git add -A`
- `$ git commit -m "bootstrapped"`
- `$ git push` # Will trigger CodePipeline & deploy/train SageMaker pipeline
- Approve the resulting model in SageMaker Studio under Model Groups of the SageMaker Project