"""MongoDB connection provider with singleton lifecycle."""
from pymongo import MongoClient, TEXT, ASCENDING, DESCENDING

from src.utils.services.aws.appconfig_service import get_config_service
from src.utils.singleton import Singleton


class MongoDBProvider(metaclass=Singleton):
    """Provides MongoDB connections and ensures indexes exist."""

    def __init__(self):
        config = get_config_service()
        host = config.get("mongodb.host", "mongodb")
        port = int(config.get("mongodb.port", 27017))
        database = config.get("mongodb.database", "contentpulse")

        self._client = MongoClient(host=host, port=port)
        self._db = self._client[database]

        self._ensure_indexes()

    def _ensure_indexes(self):
        articles = self._db["articles"]
        articles.create_index(
            [("entities.normalized", ASCENDING), ("published_at", DESCENDING)],
            name="entity_date"
        )
        articles.create_index(
            [("categories", ASCENDING), ("published_at", DESCENDING)],
            name="category_date"
        )
        articles.create_index(
            [("source", ASCENDING), ("source_id", ASCENDING)],
            unique=True,
            name="source_unique"
        )
        articles.create_index(
            [("published_at", DESCENDING)],
            name="date_desc"
        )
        articles.create_index(
            [("entities.type", ASCENDING), ("published_at", DESCENDING)],
            name="entity_type_date"
        )
        articles.create_index(
            [("summary", TEXT), ("title", TEXT)],
            name="text_search"
        )

    @property
    def db(self):
        return self._db

    @property
    def articles_collection(self):
        return self._db["articles"]

    def is_healthy(self) -> bool:
        try:
            self._client.admin.command("ping")
            return True
        except Exception:
            return False
