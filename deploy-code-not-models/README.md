# Deploy code note models

This is a new MLOps design paradigm in which instead of promoting trained ML models across accounts, the whole underlying code is promoted and the model is re-trained with data in the new account


### Workflow including tooling account:
- Commiting to the build repo (in tooling acc), triggers the build pipeline (in tooling account)
- Build pipeline triggers SM pipeline (in dev) which ends with a model registered to Model Registry Dev (in tooling)
- Approving the model triggeres the dev deploy pipeline (in tooling) which creates the infrastructure in the dev account
- Manually approving the build pipeline step (in tooling), triggers the SM pipeline for staging (in stg account)
- The SM pipeline registers a model in Model Registry Staging (in tooling account)
- Approving the model version triggers the staging deploy pipeline (in tooling) which craetes the infrastructure in staging account
(Repeat for Prod)


### Resources in tooling: 
- 2 Code repos
- 3 Deploy Pipelines
- 3 Model Registries
- 3 Event triggers (trigger deploy on model approval)
- 1 Build pipeline