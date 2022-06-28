# Multi Model Endpoint Deployment Pipeline

## Purpose

The purpose of this template is to deploy a multi-model inference endpoint. It accepts as input the S3 path where the different models are stored. All of the models need to be at the root of the path provided, and they must all be `.tar.gz` files.

## Architecture

![mme-project.png](images/mme-project.png)

## Instructions


Part 1: Create initial Service Catalog Product

1. To create the Service Catalog product for this project, download the `create-mme-product.yaml` and upload it into your CloudFormation console: https://console.aws.amazon.com/cloudformation/home?#/stacks/create/template


2. Update the Parameters section:

    - Supply a unique name for the stack

        ![](images/mme-params-01.png)

    - Enter your Service Catalog portfolio id, which can be found in the __Outputs__ tab of your deployed portfolio stack or in the Service Catalog portfolio list: https://console.aws.amazon.com/servicecatalog/home?#/portfolios

        ![](images/mme-params-02.png)

    - Update the Product Information. The product name and description are visible inside of SageMaker Studio. Other fields are visible to users that consume this directly through Service Catalog. 

    - Support information is not available inside of SageMaker Studio, but is available in the Service Catalog Dashboard.

    - Updating the source code repository information is only necessary if you forked this repo and modified it.

        ![](images/mme-params-05.png)

3. Choose __Next__, __Next__ again, check the box acknowledging that the template will create IAM resources, and then choose __Create Stack__.

4. Your template should now be visible inside of SageMaker Studio.


Part 2: Deploy the Project inside of SageMaker Studio

1. Open SageMaker Studio and sign in to your user profile.

1. Choose the SageMaker __components and registries__ icon on the left, and choose the __Create project__ button.

1. The default view displays SageMaker templates. Switch to the __Organization__ templates tab to see custom project templates.

1. The template you created will be displayed in the template list. (If you do not see it yet, make sure the correct execution role is added to the product and the __sagemaker:studio-visibility__ tag with a value of __true__ is added to the Service Catalog product).

1. Choose the template and click Select the correct project template.

    ![](../images/sm-projects-listing.png)

6. Fill out the required fields for this project.

    - __Name:__ A unique name for the project deployment.

    - __Description:__ Project description for this deployment.

7. Choose __Create Project__.

    ![](images/mme-create-project.png)

8. After a few minutes, your example project should be deployed and ready to use.