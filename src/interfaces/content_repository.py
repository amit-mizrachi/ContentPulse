"""Content Repository Interface - defines the contract for article storage."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.objects.content.processed_article import ProcessedArticle


class ContentRepository(ABC):
    """Interface for storing and querying processed articles."""

    @abstractmethod
    def store_article(self, article: ProcessedArticle) -> Dict[str, Any]:
        pass

    @abstractmethod
    def article_exists(self, source: str, source_id: str) -> bool:
        pass

    @abstractmethod
    def query_articles(
        self,
        entities: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        entity_type: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def search_articles(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        pass
