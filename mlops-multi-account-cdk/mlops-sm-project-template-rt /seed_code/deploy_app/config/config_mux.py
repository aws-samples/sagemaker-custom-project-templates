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

from pathlib import Path

from dataclasses import dataclass
from aws_cdk import Stack, Stage
import constructs
from yamldataclassconfig.config import YamlDataClassConfig
from abc import ABCMeta


DEFAULT_STAGE_NAME = "dev"
DEFAULT_STACK_NAME = "dev"


def get_config_for_stage(scope: constructs, path: str):

    default_path = Path(__file__).parent.joinpath(DEFAULT_STAGE_NAME, path)
    if stage_name := Stage.of(scope).stage_name:
        config_path = Path(__file__).parent.joinpath(stage_name.lower(), path)

        if not config_path.exists():
            print(f"Config file {path} for stage {stage_name} not found. Using {default_path} instead")
            config_path = default_path

        return config_path
    else:
        print(f"Stack created without a stage, config {path} not found. Using {default_path} instead")
        return default_path


def get_config_for_stack(scope: constructs, path: str):

    default_path = Path(__file__).parent.joinpath(DEFAULT_STACK_NAME, path)
    if stack_name := Stack.of(scope).stack_name:
        config_path = Path(__file__).parent.joinpath(stack_name.lower(), path)

        if not config_path.exists():
            print(f"Config file {path} for stack {stack_name} not found. Using {default_path} instead")
            config_path = default_path

        return config_path
    else:
        print(f"Stack created without a stack, config {path} not found. Using {default_path} instead")
        return default_path


@dataclass
class StageYamlDataClassConfig(YamlDataClassConfig, metaclass=ABCMeta):
    """This class implements YAML file load function with relative config paths and stage specific config loading capabilities."""

    def load(self):
        """
        This method automatically uses the config from alpha
        """
        path = Path(__file__).parent().joinpath("config/", "dev", self.FILE_PATH)
        return super().load(path=path)

    def load_for_stage(self, scope):
        """
        Looks up the stage from the current scope and loads the relevant config file
        """
        path = get_config_for_stage(scope, self.FILE_PATH)
        return super().load(path=path)

    def load_for_stack(self, scope):
        """
        Looks up the stack from the current scope and loads the relevant config file
        """
        path = get_config_for_stack(scope, self.FILE_PATH)
        return super().load(path=path)
