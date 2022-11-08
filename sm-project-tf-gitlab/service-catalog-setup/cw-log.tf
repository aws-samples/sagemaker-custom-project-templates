#----------------------------------------------------------#
# This component is used to create the CloudWatch Log Group
# This will have all the logs of the Terraform execution 
# associated with the SageMaker Projects
#----------------------------------------------------------#

resource "aws_cloudwatch_log_group" "command_runner_logs" {
  name = "${local.cmn_res_name}-gitlab"

}