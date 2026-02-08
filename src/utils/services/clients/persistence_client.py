"""HTTP client for persistence service."""
from functools import lru_cache
from typing import Any, Dict, List, Optional

import httpx

from src.interfaces.persistence_gateway import PersistenceGateway
from src.utils.services.aws.appconfig_service import get_config_service


class PersistenceClient(PersistenceGateway):
    """HTTP client for persistence service."""

    def __init__(self):
        appconfig = get_config_service()
        persistence_host = appconfig.get("services.persistence.host", "persistence-service")
        persistence_port = appconfig.get("services.persistence.port", 8002)
        self._base_url = f"http://{persistence_host}:{persistence_port}"
        self._client = httpx.Client(timeout=30.0)

    def create_history(self, history_data: Dict[str, Any]) -> Dict[str, Any]:
        response = self._client.post(
            f"{self._base_url}/history",
            json=history_data
        )
        response.raise_for_status()
        return response.json()

    def get_history(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        response = self._client.get(f"{self._base_url}/history", params=params)
        response.raise_for_status()
        return response.json()

    def get_history_by_request_id(self, request_id: str) -> Optional[Dict[str, Any]]:
        response = self._client.get(f"{self._base_url}/history/{request_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    def is_healthy(self) -> bool:
        try:
            response = self._client.get(f"{self._base_url}/health")
            return response.status_code == 200
        except Exception:
            return False


@lru_cache(maxsize=1)
def get_persistence_gateway() -> PersistenceClient:
    """Get the singleton PersistenceClient instance."""
    return PersistenceClient()
