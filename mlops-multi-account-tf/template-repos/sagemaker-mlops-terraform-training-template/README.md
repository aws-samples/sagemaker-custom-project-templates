## MLOps for SageMaker Model Training


The template provides a starting point for bringing your SageMaker Pipeline development to production. It can be modified and its functionalities can be extended according to the use case, being a fully customizable template. This code repository is created as part of creating a Project in SageMaker.

In this repository you can find the necessary files to create a SageMaker Pipeline. It is automated with a GitHub Action workflow, therefore when the repository is pushed, it is triggered the SageMaker pipeline execution.

The following section provides an overview of how the code is organized and what you need to modify. In particular, `pipelines/pipelines.py` contains the core of the business logic for this problem. It has the code to express the ML steps involved in generating an ML model. You will also find the code for that supports preprocessing and evaluation steps in `preprocess.py` and `evaluate.py` files respectively.

Once you understand the code structure described below, you can inspect the code and you can start customizing it for your own business case. This is only sample code, and you own this repository for your business use case. Please go ahead, modify the files, commit them and see the changes kick off the SageMaker pipelines in the CICD system.

You can also use the `sagemaker-pipelines-project.ipynb` notebook to experiment from SageMaker Studio before you are ready to checkin your code.

### Environment secrets

In order to get environment variables from AWS for the workflow execution, it is set environment secrets when the template repository is cloned for the specific project. They are used in the GitHub Action workflow.
The environment secrets are:

ARTIFACT_BUCKET: S3 bucket arn created for the SageMaker Project

AWS_REGION: AWS account region

SAGEMAKER_PIPELINE_ROLE_ARN: IAM role arn to execute the pipeline

SAGEMAKER_PROJECT_ARN: Arn of the SageMaker project

SAGEMAKER_PROJECT_ID: ID of the SageMaker project

SAGEMAKER_PROJECT_NAME_ID: Name +ID of the SageMaker project

SAGEMAKER_PROJECT_NAME: Name of the SageMaker project

AWS_DEV_ACCOUNT_NUMBER: Account ID of the training AWS account

### Repository structure

```
|-- .github/workflows
|   |-- train.yml
|-- CONTRIBUTING.md
|-- pipelines
|   |-- abalone
|   |   |-- evaluate.py
|   |   |-- __init__.py
|   |   |-- pipeline.py
|   |   `-- preprocess.py
|   |-- get_pipeline_definition.py
|   |-- __init__.py
|   |-- run_pipeline.py
|   |-- _utils.py
|   `-- __version__.py
|-- README.md
|-- setup.cfg
|-- setup.py
|-- tests
|   `-- test_pipelines.py
`-- tox.ini
```

A description of some of the artifacts is provided below:
<br/><br/>
This file contains the instructions needed to kick off an execution of the SageMaker Pipeline in the CICD system (via Git Actions).

```
|-- .github/workflows
|   |-- train.yml
```

In the `train.yml` are defined the workflow steps to run the pipeline execution. It is executed on push in the main branch. The steps are:

- Assume AWS OIDC IAM Role
- Install dependencies
- Run pipeline excution

<br/><br/>

The implementation of the pipeline steps, which includes:

```
|-- pipelines
|   |-- abalone
|   |   |-- evaluate.py
|   |   |-- __init__.py
|   |   |-- pipeline.py
|   |   `-- preprocess.py

```

- a `pipeline.py` module defining the required `get_pipeline` method that returns an instance of a SageMaker pipeline. You can use this file changing only the `get_pipeline` method for your specific pipeline steps
- a preprocessing script `preprocess.py` that is used in feature engineering in the Processor Step
- a model evaluation script `evaluate.py` to measure the Mean Squared Error of the model that's trained by the pipeline in the Evaluation step

This is the core business logic, and if you want to create your own Project, you can create your own folder for your own business problem, you can do so, and implement the `get_pipeline` interface as is in the abalone folder.

<br/><br/>
Utility modules for getting pipeline definition jsons and running pipelines (you do not typically need to modify these):

```
|-- pipelines
|   |-- get_pipeline_definition.py
|   |-- __init__.py
|   |-- run_pipeline.py
|   |-- _utils.py
|   `-- __version__.py
```

<br/><br/>
Python package artifacts:

```
|-- setup.cfg
|-- setup.py
```

<br/><br/>
A stubbed testing module for testing your pipeline as you develop:

```
|-- tests
|   `-- test_pipelines.py
```

<br/><br/>
The `tox` testing framework configuration:

```
`-- tox.ini
```

## Dataset for the Example Abalone Pipeline

The dataset used is the [UCI Machine Learning Abalone Dataset](https://archive.ics.uci.edu/ml/datasets/abalone) [1]. The aim for this task is to determine the age of an abalone (a kind of shellfish) from its physical measurements. At the core, it's a regression problem.

The dataset contains several features - length (longest shell measurement), diameter (diameter perpendicular to length), height (height with meat in the shell), whole_weight (weight of whole abalone), shucked_weight (weight of meat), viscera_weight (gut weight after bleeding), shell_weight (weight after being dried), sex ('M', 'F', 'I' where 'I' is Infant), as well as rings (integer).

The number of rings turns out to be a good approximation for age (age is rings + 1.5). However, to obtain this number requires cutting the shell through the cone, staining the section, and counting the number of rings through a microscope -- a time-consuming task. However, the other physical measurements are easier to determine. We use the dataset to build a predictive model of the variable rings through these other physical measurements.

We'll upload the data to a bucket we own. But first we gather some constants we can use later throughout the notebook.

[1] Dua, D. and Graff, C. (2019). [UCI Machine Learning Repository](http://archive.ics.uci.edu/ml). Irvine, CA: University of California, School of Information and Computer Science.
