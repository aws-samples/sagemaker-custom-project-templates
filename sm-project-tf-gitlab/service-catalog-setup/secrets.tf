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

#-------------------------------------------------#
# Create a Secrets Manager Secret
# This is used to store for Gitlab IAM Access Key credentials
#-------------------------------------------------#

resource "aws_secretsmanager_secret" "git_iam_access_key_secret" {
  name        = "${local.cmn_res_name}-gitlab-iam-access-key"
  description = "Secret for ML Gitlab IAM Access Key"
}

resource "aws_secretsmanager_secret_version" "git_iam_access_key_version" {
  secret_id     = aws_secretsmanager_secret.git_iam_access_key_secret.id
  secret_string = var.gitlab_iam_access_key
}

#-------------------------------------------------#
# Create a Secrets Manager Secret
# This is used to store for Gitlab IAM Secret Key credentials
#-------------------------------------------------#

resource "aws_secretsmanager_secret" "git_iam_secret_key_secret" {
  name        = "${local.cmn_res_name}-gitlab-iam-secret-key"
  description = "Secret for ML Gitlab IAM Secret Key"
}

resource "aws_secretsmanager_secret_version" "git_iam_secret_key_version" {
  secret_id     = aws_secretsmanager_secret.git_iam_secret_key_secrett.id
  secret_string = var.gitlab_iam_secret_key
}