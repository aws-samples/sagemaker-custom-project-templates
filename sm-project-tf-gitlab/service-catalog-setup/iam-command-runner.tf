#------------------------------------------------------------------#
# This component is used to Create the Command Runner IAM Resources
#------------------------------------------------------------------#

data "template_file" "c_runner_role_template" {
  template = file("templates/command-runner-exec-role.json")
  vars = {
    pass_role_arn = "arn:aws:iam::${local.account_id}:${var.cm_exec_pass_role_arn}"
  }
}

resource "aws_iam_policy" "c_runner_iam_policy" {
  name   = "${local.cmn_res_name}-command-runner-exec"
  policy = data.template_file.c_runner_role_template.rendered
}

resource "aws_iam_role" "c_runner_iam_role" {
  name               = var.command_runner_exec_role
  path               = "/CloudFormation/"
  description        = "Role to be Assumed by Command Runner"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {"Service": "ec2.amazonaws.com"},
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_iam_policy_attachment" "c_runner_policy_attachment" {
  depends_on = [aws_iam_role.c_runner_iam_role]
  name       = local.cmn_res_name
  roles      = [aws_iam_role.c_runner_iam_role.name]
  policy_arn = aws_iam_policy.c_runner_iam_policy.arn
}

resource "aws_iam_instance_profile" "c_runner_instance_profile" {
  depends_on = [aws_iam_role.c_runner_iam_role]
  name       = var.command_runner_exec_role
  role       = aws_iam_role.c_runner_iam_role.name
}

