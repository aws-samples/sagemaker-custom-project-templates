# MLOps Multi Account Setup with AWS CDK

As enterprise businesses embrace Machine Learning (ML) across their organisations, manual workflows for building, training, and deploying ML models tend to become bottlenecks to innovation. To overcome this, enterprises needs to shape a clear operating model defining how multiple personas, such as Data Scientists, Data Engineers, ML Engineers, IT, and Business stakeholders, should collaborate and interact, how to separate the concerns, responsibilities and skills, and how to leverage AWS services optimally. This combination of ML and Operations, so-called MLOps, is helping companies streamline their end-to-end ML lifecycle and boost productivity of data scientists while maintaining high model accuracy and enhancing security and compliance.

In this repository, we have created a baseline infrastructure for a secure MLOps environment based on CDK. Our solution consists of two parts:

 - [mlops-infra](mlops-infra/): The necessary secure infrastructure for the multiple accounts of MLOps including VPCs and VPC endpoints, SSM, IAM user roles, etc.

 - [mlops-sm-project-template](mlops-sm-project-template/): A Service Catalog portfolio that contains custom Amazon SageMaker Project templates that enable multi account model promotion.

## How to use:

First deploy [mlops-infra](mlops-infra/):

[mlops-infra](mlops-infra/) will deploy a Secure data science exploration environment for your data scientists to explore and train their models inside a SageMaker studio environment.
It also prepares your dev/preprod/prod accounts with the networking setup to: either run SageMaker studio in a VPC, or be able to create SageMaker Endpoints and other infrastructure inside VPCs.
Please note that the networking created by `mlops_infra` is a kick start example and that the repository is also designed to be able to import existing VPCs created by your organization instead of creating its own VPCs.
The repository will also create example SageMaker users (Lead Data Scientist and Data Scientist) and associated roles and policies.

Once you have deployed [mlops-infra](mlops-infra/), deploy [mlops-sm-project-template](mlops-sm-project-template/):

[mlops-sm-project-template](mlops-sm-project-template/) will create a Service Catalog portfolio that contains SageMaker project templates as Service Catalog products.
To do so, the `service_catalog` stack iterates over a `templates` folder which contains your different organization SageMaker project templates in the form of CDK stacks.
The general idea of what those templates creates is explained in [mlops-sm-project-template](mlops-sm-project-template/).
These example SageMaker project templates can be customized for the need of your organization.

## Contacts

If you have any comments or questions, please contact:

The maintaining Team: 

Viktor Malesevic <malesv@amazon.de>

Fotinos Kyriakides <kyriakf@amazon.com>

Gabija Pasiunaite <gabipas@amazon.ch>

Selena Tabbara <sttabbar@amazon.co.uk>

Sokratis Kartakis <kartakis@amazon.com>

Georgios Schinas <schinasg@amazon.co.uk>

# Special thanks

Fatema Alkhanaizi, who is no longer aws but has been the major initial contributor of the project.