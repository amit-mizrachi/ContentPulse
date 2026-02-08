"""HTTP client for MongoDB service."""
from functools import lru_cache
from typing import Any, Dict, List, Optional

import httpx

from src.interfaces.content_repository import ContentRepository
from src.objects.content.processed_article import ProcessedArticle
from src.utils.services.aws.appconfig_service import get_config_service


class MongoDBClient(ContentRepository):
    """HTTP client wrapping the MongoDB service REST API."""

    def __init__(self):
        appconfig = get_config_service()
        host = appconfig.get("services.mongodb.host", "mongodb-service")
        port = appconfig.get("services.mongodb.port", 8002)
        self._base_url = f"http://{host}:{port}"
        self._client = httpx.Client(timeout=30.0)

    def store_article(self, article: ProcessedArticle) -> Dict[str, Any]:
        response = self._client.post(
            f"{self._base_url}/articles",
            json=article.model_dump(mode="json")
        )
        response.raise_for_status()
        return response.json()

    def article_exists(self, source: str, source_id: str) -> bool:
        response = self._client.get(
            f"{self._base_url}/articles/exists",
            params={"source": source, "source_id": source_id}
        )
        response.raise_for_status()
        return response.json()["exists"]

    def query_articles(
        self,
        entities: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"limit": limit}
        if entities:
            params["entities"] = ",".join(entities)
        if categories:
            params["categories"] = ",".join(categories)
        if sources:
            params["sources"] = ",".join(sources)
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to

        response = self._client.get(f"{self._base_url}/articles", params=params)
        response.raise_for_status()
        return response.json()

    def search_articles(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        response = self._client.get(
            f"{self._base_url}/articles/search",
            params={"q": query, "limit": limit}
        )
        response.raise_for_status()
        return response.json()

    def is_healthy(self) -> bool:
        try:
            response = self._client.get(f"{self._base_url}/health")
            return response.status_code == 200
        except Exception:
            return False


@lru_cache(maxsize=1)
def get_content_repository() -> MongoDBClient:
    """Get the singleton MongoDBClient instance."""
    return MongoDBClient()
