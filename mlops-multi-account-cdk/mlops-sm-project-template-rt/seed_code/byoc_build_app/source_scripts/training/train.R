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


library(readr)

prefix <- '/opt/ml/'

input_path <- paste0(prefix , 'input/data/train/')
output_path <- paste0(prefix, 'output/')
model_path <- paste0(prefix, 'model/')
code_path <- paste(prefix, 'code', sep='/')
inference_code_dir <- paste(model_path, 'code', sep='/')


abalone_train <- read_csv(paste0(input_path, 'abalone_train.csv'))
abalone_valid <- read_csv(paste0(input_path, 'abalone_valid.csv'))

regressor = lm(formula = rings ~ female + male + length + diameter + height + whole_weight + shucked_weight + viscera_weight + shell_weight, data = abalone_train)
summary(regressor)

y_pred= predict(regressor, newdata=abalone_valid[,-1])
rmse <- sqrt(mean(((abalone_valid[,1] - y_pred)^2)[,]))
print(paste0("Calculated validation RMSE: ",rmse,";"))


# Save trained model
save(regressor, file = paste0(model_path,"model"))

# Save inference code to be used with model
# find the files that you want
list_of_files <- list.files(code_path)

# copy the files to the new folder
dir.create(inference_code_dir)
file.copy(list_of_files, inference_code_dir, recursive=TRUE)

print("successfully saved model & code")