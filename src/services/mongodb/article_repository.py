"""Article repository backed by MongoDB."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.interfaces.content_repository import ContentRepository
from src.objects.content.processed_article import ProcessedArticle
from src.services.mongodb.mongodb_provider import MongoDBProvider


class ArticleRepository(ContentRepository):
    """MongoDB-backed article storage and querying."""

    def __init__(self, provider: MongoDBProvider = None):
        self._provider = provider or MongoDBProvider()
        self._collection = self._provider.articles_collection

    def store_article(self, article: ProcessedArticle) -> Dict[str, Any]:
        doc = article.model_dump(mode="json")
        self._collection.update_one(
            {"source": article.source, "source_id": article.source_id},
            {"$set": doc},
            upsert=True
        )
        return doc

    def article_exists(self, source: str, source_id: str) -> bool:
        return self._collection.count_documents(
            {"source": source, "source_id": source_id},
            limit=1
        ) > 0

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
        query: Dict[str, Any] = {}

        if entities:
            query["entities.normalized"] = {"$in": entities}
        if categories:
            query["categories"] = {"$in": categories}
        if sources:
            query["source"] = {"$in": sources}
        if entity_type:
            query["entities.type"] = entity_type

        date_filter: Dict[str, Any] = {}
        if date_from:
            date_filter["$gte"] = date_from
        if date_to:
            date_filter["$lte"] = date_to
        if date_filter:
            query["published_at"] = date_filter

        cursor = self._collection.find(
            query, {"_id": 0}
        ).sort("published_at", -1).limit(limit)

        return list(cursor)

    def search_articles(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        cursor = self._collection.find(
            {"$text": {"$search": query}},
            {"_id": 0, "score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(limit)

        return list(cursor)

    def is_healthy(self) -> bool:
        return self._provider.is_healthy()
