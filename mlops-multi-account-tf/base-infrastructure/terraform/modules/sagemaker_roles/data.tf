data "aws_iam_policy" "AmazonSSMReadOnlyAccess" {
  arn = "arn:aws:iam::aws:policy/AmazonSSMReadOnlyAccess"
}
data "aws_iam_policy" "AWSLambda_ReadOnlyAccess" {
  arn = "arn:aws:iam::aws:policy/AWSLambda_ReadOnlyAccess"
}
data "aws_iam_policy" "AWSCodeCommitReadOnly" {
  arn = "arn:aws:iam::aws:policy/AWSCodeCommitReadOnly"
}
data "aws_iam_policy" "AmazonEC2ContainerRegistryReadOnly" {
  arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}
data "aws_iam_policy" "AmazonSageMakerFullAccess" {
  arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}