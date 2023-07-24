# Training SageMaker Pipeline

This SageMaker Pipeline definition creates a workflow that will:
- Prepare the Abalone dataset through a SageMaker Processing Job
- Train an XGBoost algorithm on the train set
- Evaluate the performance of the trained XGBoost algorithm on the validation set
- If the performance reaches a specified threshold, send the model for Manual Approval to SageMaker Model Registry.
