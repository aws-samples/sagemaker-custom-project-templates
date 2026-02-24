"""XGBoost training script with optional MLflow autologging.

This script runs in SageMaker's XGBoost framework container (script mode).
When MLFLOW_TRACKING_ARN is set as an environment variable, MLflow autologging
is enabled to track hyperparameters, metrics, and the trained model artifact.
"""
import argparse
import json
import logging
import os
import pickle

import numpy as np
import pandas as pd
import xgboost as xgb

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


def _setup_mlflow():
    """Configure MLflow tracking if MLFLOW_TRACKING_ARN is set."""
    from mlflow_helper import setup_mlflow
    mlflow_enabled = setup_mlflow("TrainAbaloneModel")
    if mlflow_enabled:
        try:
            import mlflow
            mlflow.xgboost.autolog(log_models=True, log_datasets=True)
        except Exception as e:
            logger.warning("Failed to enable XGBoost autolog: %s", e)
    return mlflow_enabled


def _end_mlflow(mlflow_enabled):
    """End MLflow runs if tracking was enabled."""
    from mlflow_helper import end_mlflow
    end_mlflow(mlflow_enabled)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # XGBoost hyperparameters
    parser.add_argument("--max_depth", type=int, default=5)
    parser.add_argument("--eta", type=float, default=0.2)
    parser.add_argument("--gamma", type=int, default=4)
    parser.add_argument("--min_child_weight", type=int, default=6)
    parser.add_argument("--subsample", type=float, default=0.7)
    parser.add_argument("--objective", type=str, default="reg:linear")
    parser.add_argument("--num_round", type=int, default=50)

    # SageMaker specific arguments
    parser.add_argument("--model-dir", type=str, default=os.environ.get("SM_MODEL_DIR", "/opt/ml/model"))
    parser.add_argument("--train", type=str, default=os.environ.get("SM_CHANNEL_TRAIN", "/opt/ml/input/data/train"))
    parser.add_argument("--validation", type=str, default=os.environ.get("SM_CHANNEL_VALIDATION", "/opt/ml/input/data/validation"))

    args = parser.parse_args()

    mlflow_enabled = _setup_mlflow()

    logger.info("Loading training data.")
    train_files = [os.path.join(args.train, f) for f in os.listdir(args.train) if f.endswith(".csv")]
    train_df = pd.concat([pd.read_csv(f, header=None) for f in train_files])
    y_train = train_df.iloc[:, 0].to_numpy()
    X_train = train_df.iloc[:, 1:].to_numpy()
    dtrain = xgb.DMatrix(X_train, label=y_train)

    logger.info("Loading validation data.")
    val_files = [os.path.join(args.validation, f) for f in os.listdir(args.validation) if f.endswith(".csv")]
    val_df = pd.concat([pd.read_csv(f, header=None) for f in val_files])
    y_val = val_df.iloc[:, 0].to_numpy()
    X_val = val_df.iloc[:, 1:].to_numpy()
    dval = xgb.DMatrix(X_val, label=y_val)

    params = {
        "max_depth": args.max_depth,
        "eta": args.eta,
        "gamma": args.gamma,
        "min_child_weight": args.min_child_weight,
        "subsample": args.subsample,
        "objective": args.objective,
    }

    logger.info("Training XGBoost model with params: %s", json.dumps(params))
    watchlist = [(dtrain, "train"), (dval, "validation")]
    model = xgb.train(
        params=params,
        dtrain=dtrain,
        evals=watchlist,
        num_boost_round=args.num_round,
    )

    # Save model artifact
    model_path = os.path.join(args.model_dir, "xgboost-model")
    pickle.dump(model, open(model_path, "wb"))
    logger.info("Model saved to %s", model_path)

    _end_mlflow(mlflow_enabled)