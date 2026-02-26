"""Training step: XGBoost model training with MLflow autologging."""
import os
from sagemaker.mlops.workflow.function_step import step


def build_train_step(instance_type):
    """Return a @step-decorated training function."""

    @step(name="TrainAbaloneModel", instance_type=instance_type, keep_alive_period_in_seconds=900)
    def train(
        train_s3_path: str,
        validation_s3_path: str,
        experiment_name: str,
        run_id: str,
        tracking_arn: str,
    ) -> tuple:
        import logging
        import numpy as np
        import pandas as pd
        import xgboost as xgb

        logger = logging.getLogger(__name__)

        # --- Load data ---
        train_df = pd.read_csv(train_s3_path, header=None)
        val_df = pd.read_csv(validation_s3_path, header=None)

        y_train = train_df.iloc[:, 0].to_numpy()
        X_train = train_df.iloc[:, 1:].to_numpy()
        y_val = val_df.iloc[:, 0].to_numpy()
        X_val = val_df.iloc[:, 1:].to_numpy()

        dtrain = xgb.DMatrix(X_train, label=y_train)
        dval = xgb.DMatrix(X_val, label=y_val)

        params = {
            "objective": "reg:linear",
            "max_depth": 5,
            "eta": 0.2,
            "gamma": 4,
            "min_child_weight": 6,
            "subsample": 0.7,
        }
        num_round = 50

        # --- MLflow: child run for training ---
        training_run_id = ""
        if tracking_arn and run_id:
            try:
                import mlflow
                mlflow.set_tracking_uri(tracking_arn)
                mlflow.set_experiment(experiment_name)
                with mlflow.start_run(run_id=run_id):
                    with mlflow.start_run(run_name="TrainAbaloneModel", nested=True) as child:
                        training_run_id = child.info.run_id
                        mlflow.xgboost.autolog(log_models=True, log_datasets=True)

                        model = xgb.train(
                            params=params,
                            dtrain=dtrain,
                            evals=[(dtrain, "train"), (dval, "validation")],
                            num_boost_round=num_round,
                        )
            except Exception as e:
                logger.warning("MLflow logging failed in train: %s", e)
                model = xgb.train(
                    params=params, dtrain=dtrain,
                    evals=[(dtrain, "train"), (dval, "validation")],
                    num_boost_round=num_round,
                )
        else:
            model = xgb.train(
                params=params, dtrain=dtrain,
                evals=[(dtrain, "train"), (dval, "validation")],
                num_boost_round=num_round,
            )

        # --- Predict on validation for downstream eval ---
        predictions = model.predict(dval)
        mse = float(np.mean((y_val - predictions) ** 2))

        # --- Save model artifact to S3 for SageMaker Model Registry ---
        import pickle, tarfile, tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            model_file = os.path.join(tmp_dir, "xgboost-model")
            pickle.dump(model, open(model_file, "wb"))

            tar_path = os.path.join(tmp_dir, "model.tar.gz")
            with tarfile.open(tar_path, "w:gz") as tar:
                tar.add(model_file, arcname="xgboost-model")

            from sagemaker.core.s3 import S3Uploader

            bucket = train_s3_path.split("/")[2]
            model_s3_uri = S3Uploader.upload(
                local_path=tar_path,
                desired_s3_uri=f"s3://{bucket}/model-artifacts",
            )

        return experiment_name, run_id, training_run_id, mse, model_s3_uri

    return train