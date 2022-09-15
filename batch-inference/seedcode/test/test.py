import argparse
import json
import logging
import os
import time

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
sm_client = boto3.client("sagemaker")

def start_pipeline_execution(pipeline_name, pipeline_parameters):
    execution_arn = sm_client.start_pipeline_execution(
        PipelineName=pipeline_name,
        PipelineParameters=pipeline_parameters
    )['PipelineExecutionArn']
    return execution_arn


def wait_for_pipeline_completion(pipeline_arn):
    response = sm_client.describe_pipeline_execution(
        PipelineExecutionArn=pipeline_arn
    )
    while response['PipelineExecutionStatus'] in ['Executing', 'Stopping']:
        time.sleep(15)
        response = sm_client.describe_pipeline_execution(
            PipelineExecutionArn=pipeline_arn
        )
    return response


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-level", type=str, default=os.environ.get("LOGLEVEL", "INFO").upper())
    parser.add_argument("--import-build-config", type=str, required=True)
    parser.add_argument("--export-test-results", type=str, required=True)
    parser.add_argument("--model-name", type=str, required=True)
    args, _ = parser.parse_known_args()

    # Configure logging to output the line number and message
    log_format = "%(levelname)s: [%(filename)s:%(lineno)s] %(message)s"
    logging.basicConfig(format=log_format, level=args.log_level)

    # Load the build config
    with open(args.import_build_config, "r") as f:
        config = json.load(f)

    # Create helper variables
    pipeline_name = f"{config['Parameters']['SageMakerProjectName']}-{config['Parameters']['StageName']}-BatchPipeline"
    input_path = config['Parameters']['InputPath']
    output_path = config['Parameters']['OutputPath']
    batch_instance_type = config['Parameters']['BatchInstanceType']
    batch_instance_count = config['Parameters']['BatchInstanceCount']

    # Execute the pipeline
    pipeline_parameters = [
        {'Name': 'InputPath', 'Value': input_path},
        {'Name': 'OutputPath', 'Value': output_path},
        {'Name': 'BatchInstanceType', 'Value': batch_instance_type},
        {'Name': 'BatchInstanceCount', 'Value': batch_instance_count},
        {'Name': 'ModelName', 'Value': args.model_name},
    ]
    pipeline_arn = start_pipeline_execution(
        pipeline_name=pipeline_name,
        pipeline_parameters=pipeline_parameters
    )
    outcome = wait_for_pipeline_completion(pipeline_arn)
    print(outcome)

    # Print results and write to file
    with open(args.export_test_results, "w") as f:
        json.dump(outcome, f, indent=4, default=str)

    if outcome['PipelineExecutionStatus'] == 'Failed':
        raise Exception(f'Pipeline failed. Reason: {outcome["FailureReason"]}')
