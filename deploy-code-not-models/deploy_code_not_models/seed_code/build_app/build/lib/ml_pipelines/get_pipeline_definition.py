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


"""A CLI to get pipeline definitions from pipeline modules."""
from __future__ import absolute_import

import argparse
import sys

from ml_pipelines._utils import get_pipeline_driver


def main():  # pragma: no cover
    """The main harness that gets the pipeline definition JSON.

    Prints the json to stdout or saves to file.
    """
    parser = argparse.ArgumentParser("Gets the pipeline definition for the pipeline script.")

    parser.add_argument(
        "-n",
        "--module-name",
        dest="module_name",
        type=str,
        help="The module name of the pipeline to import.",
    )
    parser.add_argument(
        "-f",
        "--file-name",
        dest="file_name",
        type=str,
        default=None,
        help="The file to output the pipeline definition json to.",
    )
    parser.add_argument(
        "-kwargs",
        "--kwargs",
        dest="kwargs",
        default=None,
        help="Dict string of keyword arguments for the pipeline generation (if supported)",
    )
    args = parser.parse_args()

    if args.module_name is None:
        parser.print_help()
        sys.exit(2)

    try:
        pipeline = get_pipeline_driver(args.module_name, args.kwargs)
        content = pipeline.definition()
        if args.file_name:
            with open(args.file_name, "w") as f:
                f.write(content)
        else:
            print(content)
    except Exception as e:  # pylint: disable=W0703
        print(f"Exception: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
