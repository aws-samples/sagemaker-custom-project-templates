#----------------------------------------------------------------#
# This component will create the DynamoDB table 
# This table is used for Terraform Backend State locking purposes
#----------------------------------------------------------------#

resource "aws_dynamodb_table" "backend" {
  name           = "${var.backend_table_prefix}-${local.account_id}"
  read_capacity  = 25
  write_capacity = 25
  hash_key       = "LockID"
  attribute {
    name = "LockID"
    type = "S"
  }
  tags = {
    Name        = "${var.backend_table_prefix}-${local.account_id}"
    Environment = var.env
  }
}