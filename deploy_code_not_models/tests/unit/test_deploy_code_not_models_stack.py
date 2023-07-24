import aws_cdk as core
import aws_cdk.assertions as assertions

from deploy_code_not_models.deploy_code_not_models_stack import DeployCodeNotModelsStack

# example tests. To run these tests, uncomment this file along with the example
# resource in deploy_code_not_models/deploy_code_not_models_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = DeployCodeNotModelsStack(app, "deploy-code-not-models")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
