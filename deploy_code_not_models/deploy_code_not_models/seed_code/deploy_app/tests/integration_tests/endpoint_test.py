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

import argparse
import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
sm_client = boto3.client("sagemaker")


def invoke_endpoint(endpoint_name):
    """
    Add custom logic here to invoke the endpoint and validate reponse
    """
    return {"endpoint_name": endpoint_name, "success": True}


def test_endpoint(endpoint_name):
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
        return invoke_endpoint(endpoint_name)
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
    endpoint_name = "{}-{}".format(config["Parameters"]["SageMakerProjectName"], config["Parameters"]["StageName"])
    results = test_endpoint(endpoint_name)

    # Print results and write to file
    logger.debug(json.dumps(results, indent=4))
    with open(args.export_test_results, "w") as f:
        json.dump(results, f, indent=4)
