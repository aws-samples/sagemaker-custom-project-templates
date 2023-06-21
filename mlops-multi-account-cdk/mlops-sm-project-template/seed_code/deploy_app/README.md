# Overview
This repository is constructed as a cdk application. The `buildspec.yaml` in this folder will run:
```
$ cdk synth
```
to generate CloudFormation templates that the CICD Pipeline (CodePipeline) will
use to deploy infrastructure in the respective aws accounts.

This repository in particular creates a SageMaker endpoint (for realtime inference) running inside a VPC.

# Explanation on VPC and Network pre-requirements
This repository however does not create the VPC. Instead it will create placeholders (CfnParameter),
reading values from Systems Manager Parameter Store (SSM) at CloudFormation deployment time in
the respective accounts (dev/preprod/prod) to create the endpoints inside a VPC.

It requires those values to be stored in the following SSM parameters in all accounts where an endpoint is deployed:
`"/vpc/subnets/private/ids"`
`"/vpc/sg/id"`

Those values are automatically created if you used the `mlops_infra` repository to
prepare your dev, preprod and prod accounts.

Additional configurations read at `cdk synth` time are stored in `config/`.


# Welcome to your CDK Python project!

This is a blank project for Python development with CDK.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!
