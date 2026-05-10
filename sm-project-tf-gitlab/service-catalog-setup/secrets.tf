#-------------------------------------------------#
# Create a Secrets Manager Secret
# This is used to store for GIT repo credentials
#-------------------------------------------------#

resource "aws_secretsmanager_secret" "git_repo_secret" {
  name        = "${local.cmn_res_name}-gitlab-token"
  description = "Secret for ML Gitlab private token"
  force_destroy = true
}

resource "aws_secretsmanager_secret_version" "git_repo_secret_version" {
  secret_id     = aws_secretsmanager_secret.git_repo_secret.id
  secret_string = var.gitlab_private_token
}

#-------------------------------------------------#
# Create a Secrets Manager Secret
# This is used to store for Gitlab IAM Access Key credentials
#-------------------------------------------------#

resource "aws_secretsmanager_secret" "git_iam_access_key_secret" {
  name        = "${local.cmn_res_name}-gitlab-iam-access-key"
  description = "Secret for ML Gitlab IAM Access Key"
  force_destroy = true
}

resource "aws_secretsmanager_secret_version" "git_iam_access_key_version" {
  secret_id     = aws_secretsmanager_secret.git_iam_access_key_secret.id
  secret_string = aws_iam_access_key.gitlab_ci_access_keys.id
}

#-------------------------------------------------#
# Create a Secrets Manager Secret
# This is used to store for Gitlab IAM Secret Key credentials
#-------------------------------------------------#

resource "aws_secretsmanager_secret" "git_iam_secret_key_secret" {
  name        = "${local.cmn_res_name}-gitlab-iam-secret-key"
  description = "Secret for ML Gitlab IAM Secret Key"
  force_destroy = true
}

resource "aws_secretsmanager_secret_version" "git_iam_secret_key_version" {
  secret_id     = aws_secretsmanager_secret.git_iam_secret_key_secret.id
  secret_string = aws_iam_access_key.gitlab_ci_access_keys.secret
}

#-------------------------------------------------#
# Create a Secrets Manager Secret
# This is used to store for Gitlab User Creds
#-------------------------------------------------#


resource "aws_secretsmanager_secret" "gitlab_user_creds" {
  name        = "${local.cmn_res_name}-gitlab-creds"
  description = "Secret for ML Github repo creds"
  force_destroy = true
}

resource "aws_secretsmanager_secret_version" "gitlab_user_creds_version" {
  secret_id     = aws_secretsmanager_secret.gitlab_user_creds.id
  secret_string = jsonencode({ username = var.gitlab_user_name, password = var.gitlab_private_token })
}
