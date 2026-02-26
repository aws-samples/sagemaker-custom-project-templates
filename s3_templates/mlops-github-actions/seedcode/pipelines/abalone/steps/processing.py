"""Preprocessing step: feature engineering and train/val/test split."""
from sagemaker.mlops.workflow.function_step import step


def build_preprocess_step(instance_type):
    """Return a @step-decorated preprocessing function."""

    @step(name="PreprocessAbaloneData", instance_type=instance_type, keep_alive_period_in_seconds=900)
    def preprocess(
        raw_data_s3_path: str,
        output_bucket: str,
        output_prefix: str,
        experiment_name: str,
        run_name: str,
        tracking_arn: str,
    ) -> tuple:
        import logging
        import numpy as np
        import pandas as pd
        import boto3
        from sklearn.compose import ColumnTransformer
        from sklearn.impute import SimpleImputer
        from sklearn.pipeline import Pipeline as SKPipeline
        from sklearn.preprocessing import StandardScaler, OneHotEncoder

        logger = logging.getLogger(__name__)

        feature_columns_names = [
            "sex", "length", "diameter", "height",
            "whole_weight", "shucked_weight", "viscera_weight", "shell_weight",
        ]
        label_column = "rings"
        feature_columns_dtype = {c: np.float64 for c in feature_columns_names if c != "sex"}
        feature_columns_dtype["sex"] = str

        # --- Download and read data ---
        bucket_name = raw_data_s3_path.split("/")[2]
        key = "/".join(raw_data_s3_path.split("/")[3:])
        local_path = "/tmp/abalone-dataset.csv"
        boto3.resource("s3").Bucket(bucket_name).download_file(key, local_path)

        df = pd.read_csv(
            local_path,
            header=None,
            names=feature_columns_names + [label_column],
            dtype={**feature_columns_dtype, label_column: np.float64},
        )

        # --- Feature engineering ---
        numeric_features = [c for c in feature_columns_names if c != "sex"]
        numeric_transformer = SKPipeline(steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ])
        categorical_transformer = SKPipeline(steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ])
        preprocessor = ColumnTransformer(transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, ["sex"]),
        ])

        y = df.pop(label_column)
        X_pre = preprocessor.fit_transform(df)
        y_pre = y.to_numpy().reshape(len(y), 1)
        X = np.concatenate((y_pre, X_pre), axis=1)

        np.random.shuffle(X)
        train, validation, test = np.split(X, [int(0.7 * len(X)), int(0.85 * len(X))])

        # --- Write splits to S3 ---
        train_path = f"s3://{output_bucket}/{output_prefix}/train/train.csv"
        val_path = f"s3://{output_bucket}/{output_prefix}/validation/validation.csv"
        test_path = f"s3://{output_bucket}/{output_prefix}/test/test.csv"

        pd.DataFrame(train).to_csv(train_path, header=False, index=False)
        pd.DataFrame(validation).to_csv(val_path, header=False, index=False)
        pd.DataFrame(test).to_csv(test_path, header=False, index=False)

        # --- MLflow: create parent run + child run for preprocessing ---
        run_id = ""
        if tracking_arn:
            try:
                import mlflow
                mlflow.set_tracking_uri(tracking_arn)
                mlflow.set_experiment(experiment_name)
                with mlflow.start_run(run_name=run_name) as parent_run:
                    run_id = parent_run.info.run_id
                    with mlflow.start_run(run_name="PreprocessAbaloneData", nested=True):
                        mlflow.log_params({
                            "input_data": raw_data_s3_path,
                            "total_rows": len(X),
                            "num_features": X.shape[1] - 1,
                            "train_rows": len(train),
                            "validation_rows": len(validation),
                            "test_rows": len(test),
                        })
            except Exception as e:
                logger.warning("MLflow logging failed in preprocess: %s", e)

        return train_path, val_path, test_path, experiment_name, run_id

    return preprocess