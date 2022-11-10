#---------------------------------------------------------------------------------------------#
# This component is used to Create the IAM Resources used for Service Catalog Launch Constraint
#---------------------------------------------------------------------------------------------#

data "template_file" "sc_launch_role_template" {
  template = file("templates/service-catalog-launch-role.json")
  vars = {
    pass_role_arn = "arn:aws:iam::${local.account_id}:${var.sc_product_launch_role}"
  }
}

resource "aws_iam_policy" "sc_launch_iam_policy" {
  name   = "${local.cmn_res_name}-service-catalog-launch"
  policy = data.template_file.sc_launch_role_template.rendered
}

resource "aws_iam_role" "sc_launch_iam_role" {
  name               = var.sc_product_launch_role
  path               = "/Launch/Constraint/"
  description        = "Role to be Assumed by Service Catalog Product Launch"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {"Service": "servicecatalog.amazonaws.com"},
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_iam_policy_attachment" "sc_launch_policy_attachment" {
  depends_on = [aws_iam_role.sc_launch_iam_role]
  name       = local.cmn_res_name
  roles      = [aws_iam_role.sc_launch_iam_role.name]
  policy_arn = aws_iam_policy.sc_launch_iam_policy.arn
}
