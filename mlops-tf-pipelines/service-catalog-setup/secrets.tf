#-------------------------------------------------#
# Create a Secrets Manager Secret
# This is used to store for GIT repo credentials
#-------------------------------------------------#

resource "aws_secretsmanager_secret" "git_repo_secret" {
  name        = "${local.cmn_res_name}-github-creds"
  description = "Secret for ML Github repo creds"
}

resource "aws_secretsmanager_secret_version" "git_repo_secret_version" {
  secret_id     = aws_secretsmanager_secret.git_repo_secret.id
  secret_string = jsonencode({ username = var.repo_user_name, password = var.repo_password })
}