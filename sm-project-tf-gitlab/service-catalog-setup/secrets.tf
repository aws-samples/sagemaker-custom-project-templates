#-------------------------------------------------#
# Create a Secrets Manager Secret
# This is used to store for GIT repo credentials
#-------------------------------------------------#

resource "aws_secretsmanager_secret" "git_repo_secret" {
  name        = "${local.cmn_res_name}-gitlab-token"
  description = "Secret for ML Gitlab private token"
}

resource "aws_secretsmanager_secret_version" "git_repo_secret_version" {
  secret_id     = aws_secretsmanager_secret.git_repo_secret.id
  secret_string = var.gitlab_private_token
}