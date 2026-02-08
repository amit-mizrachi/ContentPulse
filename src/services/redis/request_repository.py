import json
from datetime import datetime
from typing import Any, Dict, Optional

import redis

from src.interfaces.state_repository import StateRepository
from src.utils.services.aws.appconfig_service import get_config_service
from src.utils.singleton import Singleton


class RequestRepository(StateRepository, metaclass=Singleton):
    """Redis-backed implementation of StateRepository."""

    _KEY_PREFIX = "query:"

    def __init__(self):
        config = get_config_service()
        host = config.get("redis.host")
        port = config.get("redis.port")
        self._default_ttl = config.get("redis.default_ttl_seconds")

        self._client = redis.Redis(host=host, port=port, decode_responses=True)

    def create(self, request_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        key = self._make_key(request_id)
        self._client.setex(
            key,
            self._default_ttl,
            json.dumps(data)
        )
        return data

    def get(self, request_id: str) -> Optional[Dict[str, Any]]:
        key = self._make_key(request_id)
        raw = self._client.get(key)

        if not raw:
            return None

        return json.loads(raw)

    def update(self, request_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        current_data = self.get(request_id)
        if not current_data:
            return None

        current_data.update(updates)
        current_data["updated_at"] = datetime.utcnow().isoformat()

        key = self._make_key(request_id)
        ttl = self._client.ttl(key)
        actual_ttl = ttl if ttl > 0 else self._default_ttl

        self._client.setex(key, actual_ttl, json.dumps(current_data))

        return current_data

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
