# MLOps Multi Account Setup with AWS CDK

As enterprise businesses embrace Machine Learning (ML) across their organisations, manual workflows for building, training, and deploying ML models tend to become bottlenecks to innovation. To overcome this, enterprises needs to shape a clear operating model defining how multiple personas, such as Data Scientists, Data Engineers, ML Engineers, IT, and Business stakeholders, should collaborate and interact, how to separate the concerns, responsibilities and skills, and how to leverage AWS services optimally. This combination of ML and Operations, so-called MLOps, is helping companies streamline their end-to-end ML lifecycle and boost productivity of data scientists while maintaining high model accuracy and enhancing security and compliance.

In this repository, we have created a baseline infrastructure for a secure MLOps environment based on CDK. Our solution consists of two parts:

 - [mlops-infra](mlops-infra/): The necessary secure infrastructure for the multiple accounts of MLOps including VPCs and entpoints, SSM, IAM user roles, etc.

 - [mlops-sm-project-template](mlops-sm-project-template/): A custom Amazon SageMaker Project template that enable the multi account model promotion.

If you have any comments or questions, please contact:

Sokratis Kartakis <kartakis@amazon.com>

Fatema Alkhanaizi <alkhanai@amazon.com>

Georgios Schinas <schinasg@amazon.co.uk>
