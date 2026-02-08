from datetime import datetime
from typing import Optional

import redis

from src.utils.services.aws.appconfig_service import get_config_service
from src.objects.enums.processed_request import ProcessedRequest
from src.utils.singleton import Singleton


class RequestRepository(metaclass=Singleton):
    """Redis repository for ProcessedRequest objects."""

    _KEY_PREFIX = "request:"

    def __init__(self):
        config = get_config_service()
        host = config.get("redis.host")
        port = config.get("redis.port")
        self._default_ttl = config.get("redis.default_ttl_seconds")

        self._client = redis.Redis(host=host, port=port, decode_responses=True)

    def create(self, request: ProcessedRequest) -> ProcessedRequest:
        key = self._make_key(request.request_id)
        self._client.setex(
            key,
            self._default_ttl,
            request.model_dump_json()
        )
        return request

    def get(self, request_id: str) -> Optional[ProcessedRequest]:
        key = self._make_key(request_id)
        data = self._client.get(key)

        if not data:
            return None

        return ProcessedRequest.model_validate_json(data)

    def update(self, request_id: str, updates: dict) -> Optional[ProcessedRequest]:
        current_request = self.get(request_id)
        if not current_request:
            return None

        req_data = current_request.model_dump()
        req_data.update(updates)
        req_data["updated_at"] = datetime.utcnow()

        updated_request = ProcessedRequest.model_validate(req_data)

        key = self._make_key(request_id)
        ttl = self._client.ttl(key)
        actual_ttl = ttl if ttl > 0 else self._default_ttl

        self._client.setex(key, actual_ttl, updated_request.model_dump_json())

        return updated_request

    def delete(self, request_id: str) -> bool:
        key = self._make_key(request_id)
        return self._client.delete(key) > 0

    def is_healthy(self) -> bool:
        try:
            return self._client.ping()
        except Exception:
            return False

    def _make_key(self, request_id: str) -> str:
        return f"{self._KEY_PREFIX}{request_id}"
