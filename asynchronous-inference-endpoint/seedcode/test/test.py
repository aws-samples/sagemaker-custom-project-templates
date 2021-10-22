import argparse
import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

import sagemaker
import urllib, time

logger = logging.getLogger(__name__)
sm_client = boto3.client("sagemaker")
sm_runtime_client = boto3.client("sagemaker-runtime")
sagemaker_session = sagemaker.session.Session()


def invoke_endpoint(endpoint_name, input_location):
    """
    Add custom logic here to invoke the endpoint and validate reponse
    """
    response = sm_runtime_client.invoke_endpoint_async(
        EndpointName=endpoint_name, 
        InputLocation=input_location
    )
    return response['OutputLocation']

def get_output(output_location):
    output_url = urllib.parse.urlparse(output_location)
    bucket = output_url.netloc
    key = output_url.path[1:]
    while True:
        try:
            return sagemaker_session.read_s3_file(
                                        bucket=output_url.netloc, 
                                        key_prefix=output_url.path[1:])
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                print("waiting for output...")
                time.sleep(2)
                continue
            raise


def test_endpoint(endpoint_name, input_location):
    """
    Describe the endpoint and ensure InSerivce, then invoke endpoint.  Raises exception on error.
    """
    error_message = None
    try:
        # Ensure endpoint is in service
        response = sm_client.describe_endpoint(EndpointName=endpoint_name)
        status = response["EndpointStatus"]
        if status != "InService":
            error_message = f"SageMaker endpoint: {endpoint_name} status: {status} not InService"
            logger.error(error_message)
            raise Exception(error_message)

        # Output if endpoint has data capture enbaled
        endpoint_config_name = response["EndpointConfigName"]
        response = sm_client.describe_endpoint_config(EndpointConfigName=endpoint_config_name)
        if "DataCaptureConfig" in response and response["DataCaptureConfig"]["EnableCapture"]:
            logger.info(f"data capture enabled for endpoint config {endpoint_config_name}")

        # Call endpoint to handle
        output_location = invoke_endpoint(endpoint_name, input_location)
        return get_output(input_location)
    except ClientError as e:
        error_message = e.response["Error"]["Message"]
        logger.error(error_message)
        raise Exception(error_message)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-level", type=str, default=os.environ.get("LOGLEVEL", "INFO").upper())
    parser.add_argument("--import-build-config", type=str, required=True)
    parser.add_argument("--export-test-results", type=str, required=True)
    args, _ = parser.parse_known_args()

    # Configure logging to output the line number and message
    log_format = "%(levelname)s: [%(filename)s:%(lineno)s] %(message)s"
    logging.basicConfig(format=log_format, level=args.log_level)

    # Load the build config
    with open(args.import_build_config, "r") as f:
        config = json.load(f)

    # Get the endpoint name from sagemaker project name
    endpoint_name = "{}-{}".format(
        config["Parameters"]["SageMakerProjectName"], config["Parameters"]["StageName"]
    )
    output = test_endpoint(endpoint_name, config["Parameters"]["TestInputPath"])

    # Print results and write to file
    logger.debug(output)
    with open(args.export_test_results, "w") as f:
        f.write(output)
