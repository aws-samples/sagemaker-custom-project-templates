# Custom Project Templates in SageMaker

This repository contains an example SageMaker Project template. Each folder in this repo contains a custom project template with details on how what that template achieves and how to set it up. 

## Adding the template to Studio
### 1. Create a Service Catalog Portfolio
* Open the AWS Service Catalog console at https://console.aws.amazon.com/servicecatalog/
* If you are using the AWS Service Catalog administrator console for the first time, choose Launch solutions with the Getting Started library to start the wizard for configuring a portfolio. Otherwise, choose Create portfolio.
* Type the following values:
    * Portfolio name – SageMaker MLOps Templates
    * Description – Custom project templates for MLOps
    * Owner – IT (it@example.com)
* Choose Create.

### 2. Create a Service Catalog Product
* Choose and open the portfolio created in the steps above. Next choose a product and then choose Upload new product.
* On the Enter product details page, type the following and then choose Next:
    * Product name – Custom build, train, deploy project
    * Description – Bootstrapped templated for quick starting an MLOps workflow with security best practices
    * Owner – IT
    * Distributor – (blank)
* On the Version details page, choose Specify an Amazon S3 template URL, type the following, and then choose Next:
    * Select template – upload the template provided in this repo
    * Version title – v1.0
    * Description – Base Version
* On the Enter support details page, type the following and then choose Next (this information will be organization specific):
    * Email contact – ITSupport@example.com
    * Support link – https://wiki.example.com/IT/support
    * Support description – Contact the IT department for issues deploying or connecting to this product.
* On the Review page, choose Create product

### 3. Add a Launch Constraint

A launch constraint designates an IAM role that AWS Service Catalog assumes when an end user launches a product. This ensures that Service Catalog has the required permissions to provision the product (CloudFormation template). 

#### Create IAM roles
- Open the IAM Console at https://console.aws.amazon.com/iam/
- Navigate to 'Policies' and choose 'Create Policy'
    - Create the policy required to launch this template (the examples in this repo may contain sample policies to use). Make sure to update the KMS Key ARN with a customer managed key in your account. If you do not need encryption, remove the KMS policy statement (Line 7, `policies/IAM Policy - ServiceCatalogLaunch.json`), or replace the resoure ARN with "*" to allow access to all keys. 
    - Choose Next, Review policy, enter a suitable name and choose Create policy
- To create the role, choose Roles from the navigation pane
    - Choose AWS service as the Trusted entity and choose "Service Catalog"
    - Choose the policy you just created, add a Role name and choose Create role.
- Repeat the steps to create both the ServiceCatalogLaunch and ServiceCatalogUse roles.
#### Add Launch constraint
- Open Service Catalog console at https://console.aws.amazon.com/servicecatalog/
    - Choose the portfolio you created in Step 1
    - In the details page, choose Constraints tab
    - Choose Create constraint, and choose the product from Step 2
    - Choose 'Launch' as the constraint type, and choose the ServiceCatalogLaunch role you just created.
    - Add an optional description and click Create.


### 4. Making the product available in SageMaker Studio

#### Add users/roles to the Portfolio.
You can grant access to the Portfolio directly through the console, or add the `servicecatalog:ProvisionProduct` to the Studio's IAM role.

To add access through the console,
* On the portfolio details page, choose the Groups, roles, and users tab.
* Choose Add groups, roles, users.
* On the Roles tab, select the checkbox for SageMaker Studio execution role and choose Add access. Alternatively, you can use IAM groups or IAM Users through the Groups and Users tabs respectively.

#### Tags
To make your project template available in your Organization templates list in SageMaker Studio, create a tag with the following key and value to the AWS Service Catalog Product you created in step 2.

* key - sagemaker:studio-visibility
* value - true

After you complete these steps, SageMaker Studio users in your organization can create a project with the template you created by following the steps in Create an MLOps Project using Amazon SageMaker Studio and choosing Organization templates when you choose a template.

You can also add custom key-value tag pairs to restrict access to templates based on teams or users.

_Note: Ensure that the tag is added to the Product, not the Portfolio._

## Creating the project
- Open SageMaker Studio and sign in to your user profile.
- Choose the SageMaker components and registries icon on the left, and choose Create project button.
- Switch to the Organization templates tab. The default view displays SageMaker templates.
- The template you created will be displayed in the screen. (If you do not see it yet, make sure the execution role is added to the product and the sagemaker:studio-visibility tag is added exactly as described above).
- Choose the template and click Select project template.
![sagemaker-project-screen](assets/create-project.png)
- Enter a name and optional description for the project. Add the UseRoleArn (launch constraint role created in Step 3) and the KMS ARN. Optionally, add tags and choose Create project.
![sagemaker-project-template-parameters](assets/template-parameters.png)

Your project is now created and loaded with sample seed code for training and deploying a model for the abalone dataset!

## License

This library is licensed under the MIT-0 License. See the LICENSE file. 

