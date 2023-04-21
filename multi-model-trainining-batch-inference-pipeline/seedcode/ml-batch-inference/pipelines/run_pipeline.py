# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
"""A CLI to create or update and run pipelines."""
from __future__ import absolute_import

import argparse
import json
from os import pipe
import sys

from pipelines._utils import get_pipeline_driver, convert_struct, get_pipeline_custom_tags


def main(module_name, role_arn, tags, kwargs, description=''):  # pragma: no cover

    if module_name is None or role_arn is None:
        sys.exit(2)
    tags = convert_struct(tags)

    try:
        pipeline = get_pipeline_driver(module_name, kwargs)
        print("###### Creating/updating a SageMaker Pipeline with the following definition:")
        parsed = json.loads(pipeline.definition())
        print(json.dumps(parsed, indent=2, sort_keys=True))

        # all_tags = get_pipeline_custom_tags(module_name, kwargs, tags)

        # upsert_response = pipeline.upsert(
        #     role_arn=role_arn, description=description, tags=all_tags
        # )
        # print("\n###### Created/Updated SageMaker Pipeline: Response received:")
        # print(upsert_response)

        return pipeline.definition()
    except Exception as e:  # pylint: disable=W0703
        print(f"Exception: {e}")
        sys.exit(1)


if __name__ == "__main__":

    """The main harness that creates or updates and runs the pipeline.
    Creates or updates the pipeline and runs it.
    """
    parser = argparse.ArgumentParser(
        "Creates or updates and runs the pipeline for the pipeline script."
    )

    parser.add_argument(
        "-n",
        "--module-name",
        dest="module_name",
        type=str,
        help="The module name of the pipeline to import.",
    )
    parser.add_argument(
        "-kwargs",
        "--kwargs",
        dest="kwargs",
        default=None,
        help="Dict string of keyword arguments for the pipeline generation (if supported)",
    )
    parser.add_argument(
        "-role-arn",
        "--role-arn",
        dest="role_arn",
        type=str,
        help="The role arn for the pipeline service execution role.",
    )
    parser.add_argument(
        "-description",
        "--description",
        dest="description",
        type=str,
        default=None,
        help="The description of the pipeline.",
    )
    parser.add_argument(
        "-tags",
        "--tags",
        dest="tags",
        default=None,
        help="""List of dict strings of '[{"Key": "string", "Value": "string"}, ..]'""",
    )
    args = parser.parse_args()

    pipeline_arn = main(args.module_name, args.role_arn, args.tags, args.kwargs, args.description)
    print(f'Pipeline ARN: {pipeline_arn}')