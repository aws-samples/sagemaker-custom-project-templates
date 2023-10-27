import argparse
import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

LOG_FORMAT = "%(levelname)s: [%(filename)s:%(lineno)s] %(message)s"

target_acc_boto3_session = boto3.Session(profile_name="target")
target_sm_client = target_acc_boto3_session.client("sagemaker")


def invoke_endpoint(endpoint_name):
    """
    Add custom logic here to invoke the endpoint and validate reponse
    """
    return {"endpoint_name": endpoint_name, "success": True}


def test_endpoint(endpoint_name):
    """
    Describe the endpoint and ensure InSerivce, then invoke endpoint.  Raises exception on error.
    """
    try:
        # Ensure endpoint is in service
        response = target_sm_client.describe_endpoint(EndpointName=endpoint_name)
        status = response["EndpointStatus"]
        if status != "InService":
            error_message = (
                f"SageMaker endpoint: {endpoint_name} status: {status} not InService"
            )
            logger.error(error_message)
            raise Exception(error_message)

        # Output if endpoint has data capture enbaled
        endpoint_config_name = response["EndpointConfigName"]
        response = target_sm_client.describe_endpoint_config(
            EndpointConfigName=endpoint_config_name
        )
        if (
            "DataCaptureConfig" in response
            and response["DataCaptureConfig"]["EnableCapture"]
        ):
            logger.info(
                "data capture enabled for endpoint config %s", endpoint_config_name
            )

        # Call endpoint to handle
        return invoke_endpoint(endpoint_name)
    except ClientError as err:
        raise Exception("Could not invoke endpoint with boto client") from err
    except Exception as err:
        raise Exception("Invoke endpoint tests raised an error.") from err


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--log-level", type=str, default=os.environ.get("LOGLEVEL", "INFO").upper()
    )
    parser.add_argument("--endpoint-name", type=str, required=True)
    parser.add_argument("--export-test-results", type=str, required=True)
    args, _ = parser.parse_known_args()

    # Configure logging to output the line number and message
    logging.basicConfig(format=LOG_FORMAT, level=args.log_level)

    # Get the endpoint name from sagemaker project name
    results = test_endpoint(args.endpoint_name)

    # Print results and write to file
    logger.debug(json.dumps(results, indent=4))
    with open(args.export_test_results, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
