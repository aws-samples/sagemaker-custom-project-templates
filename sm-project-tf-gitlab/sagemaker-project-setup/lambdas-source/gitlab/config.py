# -*- coding: utf-8 -*-
#
# Copyright (C) 2013-2017 Gauvain Pocentek <gauvain@pocentek.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import configparser
import os
import shlex
import subprocess
from os.path import expanduser, expandvars
from typing import List, Optional, Union

from gitlab.const import USER_AGENT


def _env_config() -> List[str]:
    if "PYTHON_GITLAB_CFG" in os.environ:
        return [os.environ["PYTHON_GITLAB_CFG"]]
    return []


_DEFAULT_FILES: List[str] = _env_config() + [
    "/etc/python-gitlab.cfg",
    os.path.expanduser("~/.python-gitlab.cfg"),
]

HELPER_PREFIX = "helper:"

HELPER_ATTRIBUTES = ["job_token", "http_password", "private_token", "oauth_token"]


class ConfigError(Exception):
    pass


class GitlabIDError(ConfigError):
    pass


class GitlabDataError(ConfigError):
    pass


class GitlabConfigMissingError(ConfigError):
    pass


class GitlabConfigHelperError(ConfigError):
    pass


class GitlabConfigParser(object):
    def __init__(
        self, gitlab_id: Optional[str] = None, config_files: Optional[List[str]] = None
    ) -> None:
        self.gitlab_id = gitlab_id
        _files = config_files or _DEFAULT_FILES
        file_exist = False
        for file in _files:
            if os.path.exists(file):
                file_exist = True
        if not file_exist:
            raise GitlabConfigMissingError(
                "Config file not found. \nPlease create one in "
                "one of the following locations: {} \nor "
                "specify a config file using the '-c' parameter.".format(
                    ", ".join(_DEFAULT_FILES)
                )
            )

        self._config = configparser.ConfigParser()
        self._config.read(_files)

        if self.gitlab_id is None:
            try:
                self.gitlab_id = self._config.get("global", "default")
            except Exception as e:
                raise GitlabIDError(
                    "Impossible to get the gitlab id (not specified in config file)"
                ) from e

        try:
            self.url = self._config.get(self.gitlab_id, "url")
        except Exception as e:
            raise GitlabDataError(
                "Impossible to get gitlab informations from "
                "configuration (%s)" % self.gitlab_id
            ) from e

        self.ssl_verify: Union[bool, str] = True
        try:
            self.ssl_verify = self._config.getboolean("global", "ssl_verify")
        except ValueError:
            # Value Error means the option exists but isn't a boolean.
            # Get as a string instead as it should then be a local path to a
            # CA bundle.
            try:
                self.ssl_verify = self._config.get("global", "ssl_verify")
            except Exception:
                pass
        except Exception:
            pass
        try:
            self.ssl_verify = self._config.getboolean(self.gitlab_id, "ssl_verify")
        except ValueError:
            # Value Error means the option exists but isn't a boolean.
            # Get as a string instead as it should then be a local path to a
            # CA bundle.
            try:
                self.ssl_verify = self._config.get(self.gitlab_id, "ssl_verify")
            except Exception:
                pass
        except Exception:
            pass

        self.timeout = 60
        try:
            self.timeout = self._config.getint("global", "timeout")
        except Exception:
            pass
        try:
            self.timeout = self._config.getint(self.gitlab_id, "timeout")
        except Exception:
            pass

        self.private_token = None
        try:
            self.private_token = self._config.get(self.gitlab_id, "private_token")
        except Exception:
            pass

        self.oauth_token = None
        try:
            self.oauth_token = self._config.get(self.gitlab_id, "oauth_token")
        except Exception:
            pass

        self.job_token = None
        try:
            self.job_token = self._config.get(self.gitlab_id, "job_token")
        except Exception:
            pass

        self.http_username = None
        self.http_password = None
        try:
            self.http_username = self._config.get(self.gitlab_id, "http_username")
            self.http_password = self._config.get(self.gitlab_id, "http_password")
        except Exception:
            pass

        self._get_values_from_helper()

        self.api_version = "4"
        try:
            self.api_version = self._config.get("global", "api_version")
        except Exception:
            pass
        try:
            self.api_version = self._config.get(self.gitlab_id, "api_version")
        except Exception:
            pass
        if self.api_version not in ("4",):
            raise GitlabDataError("Unsupported API version: %s" % self.api_version)

        self.per_page = None
        for section in ["global", self.gitlab_id]:
            try:
                self.per_page = self._config.getint(section, "per_page")
            except Exception:
                pass
        if self.per_page is not None and not 0 <= self.per_page <= 100:
            raise GitlabDataError("Unsupported per_page number: %s" % self.per_page)

        self.pagination = None
        try:
            self.pagination = self._config.get(self.gitlab_id, "pagination")
        except Exception:
            pass

        self.order_by = None
        try:
            self.order_by = self._config.get(self.gitlab_id, "order_by")
        except Exception:
            pass

        self.user_agent = USER_AGENT
        try:
            self.user_agent = self._config.get("global", "user_agent")
        except Exception:
            pass
        try:
            self.user_agent = self._config.get(self.gitlab_id, "user_agent")
        except Exception:
            pass

    def _get_values_from_helper(self) -> None:
        """Update attributes that may get values from an external helper program"""
        for attr in HELPER_ATTRIBUTES:
            value = getattr(self, attr)
            if not isinstance(value, str):
                continue

            if not value.lower().strip().startswith(HELPER_PREFIX):
                continue

            helper = value[len(HELPER_PREFIX) :].strip()
            commmand = [expanduser(expandvars(token)) for token in shlex.split(helper)]

            try:
                value = (
                    subprocess.check_output(commmand, stderr=subprocess.PIPE)
                    .decode("utf-8")
                    .strip()
                )
            except subprocess.CalledProcessError as e:
                stderr = e.stderr.decode().strip()
                raise GitlabConfigHelperError(
                    f"Failed to read {attr} value from helper "
                    f"for {self.gitlab_id}:\n{stderr}"
                ) from e

            setattr(self, attr, value)
