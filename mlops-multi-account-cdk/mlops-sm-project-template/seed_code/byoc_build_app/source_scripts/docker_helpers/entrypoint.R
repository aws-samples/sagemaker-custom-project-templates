# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# SPDX-License-Identifier: MIT-0
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


library(jsonlite)
library(reticulate)
library(stringr)


args = commandArgs(trailingOnly=TRUE)
print(args)

boto3 <- import('boto3')
s3 <- boto3$client('s3')

# Setup parameters
# Container directories
prefix <- '/opt/ml'
input_path <- paste(prefix, 'input/data', sep='/')
output_path <- paste(prefix, 'output', sep='/')
model_path <- paste(prefix, 'model', sep='/')
code_dir <- paste(prefix, 'code', sep='/')
inference_code_dir <- paste(model_path, 'code', sep='/')


if (args=="train") {
  
  # This is where the hyperparamters are saved by the estimator on the container instance
  param_path <- paste(prefix, 'input/config/hyperparameters.json', sep='/')
  params <- read_json(param_path)
  
  s3_source_code_tar <- gsub('"', '', params$sagemaker_submit_directory)
  script <- gsub('"', '', params$sagemaker_program)
  
  bucketkey <- str_replace(s3_source_code_tar, "s3://", "")
  bucket <- str_remove(bucketkey, "/.*")
  key <- str_remove(bucketkey, ".*?/")
  
  s3$download_file(bucket, key, "sourcedir.tar.gz")
  untar("sourcedir.tar.gz", exdir=code_dir)
  
  print("training started")
  source(file.path(code_dir, script))
  
} else if(args=="serve"){
  print("inference time")
  source(file.path(inference_code_dir, "deploy.R"))
}
