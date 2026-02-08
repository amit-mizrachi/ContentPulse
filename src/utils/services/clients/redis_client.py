"""Redis-backed state repository client."""
from functools import lru_cache
from typing import Any, Dict, Optional

import httpx

from src.interfaces.state_repository import StateRepository
from src.utils.services.aws.appconfig_service import get_config_service
from src.objects.enums.processed_request import ProcessedRequest


class RedisClient(StateRepository):
    """Redis-backed state repository communicating via HTTP."""

    def __init__(self):
        appconfig = get_config_service()
        redis_service_host = appconfig.get("services.redis.host", "redis-service")
        redis_service_port = appconfig.get("services.redis.port", 8001)
        self._base_url = f"http://{redis_service_host}:{redis_service_port}"
        self._client = httpx.Client(timeout=30.0)

    def create(self, request_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        response = self._client.post(
            f"{self._base_url}/requests/{request_id}",
            json=data
        )
        response.raise_for_status()
        return response.json()

    def get(self, request_id: str) -> Optional[Dict[str, Any]]:
        response = self._client.get(f"{self._base_url}/requests/{request_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    def update(self, request_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        response = self._client.patch(
            f"{self._base_url}/requests/{request_id}",
            json=updates
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    def delete(self, request_id: str) -> bool:
        response = self._client.delete(f"{self._base_url}/requests/{request_id}")
        if response.status_code == 404:
            return False
        response.raise_for_status()
        return True

    def is_healthy(self) -> bool:
        try:
            response = self._client.get(f"{self._base_url}/health")
            return response.status_code == 200
        except Exception:
            return False

    def create_request(self, request: ProcessedRequest) -> ProcessedRequest:
        data = self.create(request.request_id, request.model_dump(mode="json"))
        return ProcessedRequest.model_validate(data)

    def get_request(self, request_id: str) -> Optional[ProcessedRequest]:
        data = self.get(request_id)
        if data is None:
            return None
        return ProcessedRequest.model_validate(data)

    def update_request(self, request_id: str, updates: dict) -> Optional[ProcessedRequest]:
        data = self.update(request_id, updates)
        if data is None:
            return None
        return ProcessedRequest.model_validate(data)

    def delete_request(self, request_id: str) -> bool:
        return self.delete(request_id)

    def health_check(self) -> bool:
        return self.is_healthy()


@lru_cache(maxsize=1)
def get_state_repository() -> RedisClient:
    """Get the singleton RedisClient instance."""
    return RedisClient()
