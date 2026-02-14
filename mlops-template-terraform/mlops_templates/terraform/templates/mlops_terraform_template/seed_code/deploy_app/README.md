# Terraform Deploy App

How to use:

- First Time, within SM Studio
- Git -> Open Git Repository In Terminal
- Run the following commands

```bash
make bootstrap
# tap enter for the defaults
make plan
make apply
```

Your CICD pipeline should now be deployed. Push bootstrapping changes to the repo

```
git add -A
git commit -m "bootstrapping"
git push
```

Open CodePipeline and see the pipeline execute.

## Automated Endpoint Deployment

Whenever a new model has been trained and approved by the modelbuild project, the CICD pipeline for this project will 
trigger and attempt to deploy a SageMaker Endpoint. 