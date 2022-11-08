#------------------------------------------------------------------#
# This component is used to Create the GitLab CI IAM Resources
#------------------------------------------------------------------#

data "template_file" "gitlab_ci_template" {
  template = file("templates/gitlab-ci-iam-user.json")
}

resource "aws_iam_policy" "gitlab_ci_policy" {
  name   = "${local.cmn_res_name}-gitlab-ci"
  policy = data.template_file.gitlab_ci_template.rendered
}

resource "aws_iam_user" "gitlab_ci_user" {
  name = "GitLab-CI-IAM-User"
  path = "/mlops/"
}

resource "aws_iam_user_policy_attachment" "gitlab_ci_policy_attach" {
  depends_on = [aws_iam_user.gitlab_ci_user, aws_iam_policy.gitlab_ci_policy]
  user       = aws_iam_user.gitlab_ci_user.name
  policy_arn = aws_iam_policy.gitlab_ci_policy.arn
}

resource "aws_iam_access_key" "gitlab_ci_access_keys" {
  depends_on = [aws_iam_user_policy_attachment.gitlab_ci_policy_attach]
  user       = aws_iam_user.gitlab_ci_user.name
}
