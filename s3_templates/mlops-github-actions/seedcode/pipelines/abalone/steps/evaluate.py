"""Evaluation step: load model from MLflow, compute metrics, log to MLflow."""
from sagemaker.mlops.workflow.function_step import step


def build_evaluate_step(instance_type):
    """Return a @step-decorated evaluation function."""

    @step(name="EvaluateAbaloneModel", instance_type=instance_type, keep_alive_period_in_seconds=900)
    def evaluate(
        test_s3_path: str,
        experiment_name: str,
        run_id: str,
        training_run_id: str,
        tracking_arn: str,
    ) -> dict:
        import logging
        import numpy as np
        import pandas as pd
        import xgboost
        from sklearn.metrics import mean_squared_error

        logger = logging.getLogger(__name__)

        test_df = pd.read_csv(test_s3_path, header=None)
        y_test = test_df.iloc[:, 0].to_numpy()
        X_test = xgboost.DMatrix(test_df.iloc[:, 1:].values)

        # Load model from MLflow if available
        predictions = None
        if tracking_arn and training_run_id:
            try:
                import mlflow
                mlflow.set_tracking_uri(tracking_arn)
                mlflow.set_experiment(experiment_name)
                model = mlflow.xgboost.load_model(f"runs:/{training_run_id}/model")
                predictions = model.predict(X_test)
            except Exception as e:
                logger.warning("Failed to load model from MLflow: %s", e)

        if predictions is None:
            return {"mse": 999.0}

        mse = float(mean_squared_error(y_test, predictions))
        std = float(np.std(y_test - predictions))

        # --- MLflow: child run for evaluation ---
        if tracking_arn and run_id:
            try:
                import mlflow
                with mlflow.start_run(run_id=run_id):
                    with mlflow.start_run(run_name="EvaluateAbaloneModel", nested=True):
                        mlflow.log_metrics({"mse": mse, "mse_std": std})
            except Exception as e:
                logger.warning("MLflow logging failed in evaluate: %s", e)

        return {"mse": mse}

    return evaluate