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
library(rjson)

model_path <- "/opt/ml/processing/model/"
model_file_tar <- paste0(model_path, "model.tar.gz")
model_file <- paste0(model_path, "model")

untar(model_file_tar, exdir = "/opt/ml/processing/model")

load(model_file)

test_path <- "/opt/ml/processing/test/"
abalone_test <- read_csv(paste0(test_path, 'abalone_test.csv'))


y_pred= predict(regressor, newdata=abalone_test[,-1])
rmse <- sqrt(mean(((abalone_test[,1] - y_pred)^2)[,]))
print(paste0("Calculated validation RMSE: ",rmse,";"))

report_dict = list(
  regression_metrics = list(
    rmse= list(value= rmse, standard_deviation = NA)
  )
)

output_dir = "/opt/ml/processing/evaluation/evaluation.json"

jsonData <- toJSON(report_dict)
write(jsonData, output_dir)
