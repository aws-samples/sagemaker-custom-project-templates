"""Shared MLflow helper for pipeline steps.

Provides setup/teardown for MLflow runs. Each pipeline step creates its own
run under a shared experiment (the pipeline name). When MLFLOW_TRACKING_ARN
is not set, all functions are no-ops.
"""
import logging
import os

logger = logging.getLogger(__name__)


def _install_mlflow():
    """Install MLflow dependencies at runtime if not already available."""
    try:
        import mlflow  # noqa: F401
        return True
    except ImportError:
        pass
    try:
        import subprocess
        import sys
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "mlflow", "sagemaker-mlflow==0.2.0", "-q"]
        )
        return True
    except Exception as e:
        logger.warning("Failed to install MLflow: %s", e)
        return False


def setup_mlflow(step_name):
    """Set up MLflow tracking for a pipeline step.

    Args:
        step_name: Name for this run (e.g. "PreprocessAbaloneData")

    Returns:
        True if MLflow tracking is active, False otherwise.
    """
    tracking_arn = os.environ.get("MLFLOW_TRACKING_ARN", "")
    if not tracking_arn:
        logger.info("MLFLOW_TRACKING_ARN not set. MLflow tracking disabled.")
        return False

    if not _install_mlflow():
        return False

    try:
        import mlflow

        mlflow.set_tracking_uri(tracking_arn)

        experiment_name = os.environ.get("MLFLOW_EXPERIMENT_NAME", "Default")
        mlflow.set_experiment(experiment_name)
        mlflow.start_run(run_name=step_name)

        logger.info("MLflow run started: %s (experiment=%s)", step_name, experiment_name)
        return True
    except Exception as e:
        logger.warning("Failed to set up MLflow: %s. Continuing without tracking.", e)
        return False


def end_mlflow(mlflow_enabled):
    """End the current MLflow run.

    Args:
        mlflow_enabled: Return value from setup_mlflow().
    """
    if not mlflow_enabled:
        return
    try:
        import mlflow
        mlflow.end_run()
    except Exception as e:
        logger.warning("Failed to end MLflow run: %s", e)