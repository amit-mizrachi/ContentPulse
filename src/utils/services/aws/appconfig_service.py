"""AWS AppConfig service for configuration management."""
import json
import os
from functools import lru_cache
from typing import Any, Optional

import boto3


class AppConfigService:
    """AWS AppConfig client for dynamic configuration."""

    def __init__(self):
        self._application_id = os.environ.get("APPCONFIG_APPLICATION_ID", "")
        self._environment_id = os.environ.get("APPCONFIG_ENVIRONMENT_ID", "")
        self._configuration_profile_id = os.environ.get("APPCONFIG_PROFILE_ID", "")
        region = os.environ.get("AWS_REGION", "ap-south-1")

        self._client = boto3.client("appconfigdata", region_name=region)
        self._cached_config: Optional[dict] = None
        self._next_poll_token: Optional[str] = None

    def _start_session(self) -> str:
        response = self._client.start_configuration_session(
            ApplicationIdentifier=self._application_id,
            EnvironmentIdentifier=self._environment_id,
            ConfigurationProfileIdentifier=self._configuration_profile_id
        )
        return response["InitialConfigurationToken"]

    def _fetch_configuration(self) -> dict:
        if self._next_poll_token is None:
            self._next_poll_token = self._start_session()

        response = self._client.get_latest_configuration(
            ConfigurationToken=self._next_poll_token
        )

        self._next_poll_token = response["NextPollConfigurationToken"]

        content = response["Configuration"].read()
        if content:
            self._cached_config = json.loads(content)

        return self._cached_config

    def _resolve_key(self, config: dict, key: str) -> Any:
        keys = key.split(".")
        value = config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                raise KeyError(f"Key '{key}' not found in configuration")
        return value

    def get(self, key: str, default: Any = None) -> Any:
        try:
            if self._cached_config is None:
                self._fetch_configuration()

            return self._resolve_key(self._cached_config, key)
        except KeyError:
            if default is not None:
                return default
            raise

    def refresh(self) -> dict:
        return self._fetch_configuration()


@lru_cache(maxsize=1)
def get_config_service() -> AppConfigService:
    """Get the singleton AppConfigService instance."""
    return AppConfigService()
