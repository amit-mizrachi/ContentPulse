"""MongoDB-backed article repository using direct MongoDB connection."""
from functools import lru_cache
from typing import Any, Dict, List, Optional

from pymongo import MongoClient, TEXT, ASCENDING, DESCENDING

from src.interfaces.article_store import ArticleStore
from src.objects.content.processed_article import ProcessedArticle
from src.utils.services.aws.appconfig_service import get_config_service


class MongoDBClient(ArticleStore):
    """Direct MongoDB-backed article storage and querying."""

    def __init__(self):
        config = get_config_service()
        host = config.get("mongodb.host", "mongodb")
        port = int(config.get("mongodb.port", 27017))
        database = config.get("mongodb.database", "contentpulse")

        self._client = MongoClient(host=host, port=port)
        self._db = self._client[database]
        self._collection = self._db["articles"]

        self._ensure_indexes()

    def _ensure_indexes(self):
        self._collection.create_index(
            [("entities.normalized", ASCENDING), ("published_at", DESCENDING)],
            name="entity_date"
        )
        self._collection.create_index(
            [("categories", ASCENDING), ("published_at", DESCENDING)],
            name="category_date"
        )
        self._collection.create_index(
            [("source", ASCENDING), ("source_id", ASCENDING)],
            unique=True,
            name="source_unique"
        )
        self._collection.create_index(
            [("published_at", DESCENDING)],
            name="date_desc"
        )
        self._collection.create_index(
            [("entities.type", ASCENDING), ("published_at", DESCENDING)],
            name="entity_type_date"
        )
        self._collection.create_index(
            [("summary", TEXT), ("title", TEXT)],
            name="text_search"
        )

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
        try:
            self._client.admin.command("ping")
            return True
        except Exception:
            return False


@lru_cache(maxsize=1)
def get_content_repository() -> MongoDBClient:
    """Get the singleton MongoDBClient instance."""
    return MongoDBClient()
