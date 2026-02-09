"""Tests for MongoDBArticleRepository (mocked MongoDB)."""
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from src.shared.objects.content.article_entity import ArticleEntity
from src.shared.objects.content.processed_article import ProcessedArticle


class TestMongoDBArticleRepository:
    @pytest.fixture
    def mock_mongo(self):
        """Mock MongoClient and its chain: client -> db -> collection."""
        collection = MagicMock()
        db = MagicMock()
        db.__getitem__ = MagicMock(return_value=collection)
        client = MagicMock()
        client.__getitem__ = MagicMock(return_value=db)
        client.admin.command.return_value = {"ok": 1}
        return client, db, collection

    @pytest.fixture
    def repository(self, mock_mongo):
        mock_client, mock_db, mock_collection = mock_mongo
        with patch("src.shared.repositories.mongodb_article_repository.get_config_service") as mock_config, \
             patch("src.shared.repositories.mongodb_article_repository.MongoClient", return_value=mock_client):
            mock_config.return_value.get.side_effect = lambda key, default=None: {
                "mongodb.host": "localhost",
                "mongodb.port": "27017",
                "mongodb.database": "testdb",
            }.get(key, default)

            from src.shared.repositories.mongodb_article_repository import MongoDBArticleRepository
            repo = MongoDBArticleRepository()
        return repo, mock_collection

    def test_store_article(self, repository, sample_processed_article):
        repo, mock_collection = repository
        repo.store_article(sample_processed_article)

        mock_collection.update_one.assert_called_once()
        call_args = mock_collection.update_one.call_args
        assert call_args[0][0] == {"source": "reddit", "source_id": "abc123"}

    def test_article_exists_true(self, repository):
        repo, mock_collection = repository
        mock_collection.count_documents.return_value = 1
        assert repo.article_exists("reddit", "abc123") is True

    def test_article_exists_false(self, repository):
        repo, mock_collection = repository
        mock_collection.count_documents.return_value = 0
        assert repo.article_exists("reddit", "xyz") is False

    def test_query_articles_with_entities(self, repository):
        repo, mock_collection = repository
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__ = MagicMock(return_value=iter([]))
        mock_collection.find.return_value = mock_cursor

        repo.query_articles(entities=["manchester_united"])

        find_call = mock_collection.find.call_args
        query = find_call[0][0]
        assert "entities.normalized" in query
        assert query["entities.normalized"] == {"$in": ["manchester_united"]}

    def test_search_articles(self, repository):
        repo, mock_collection = repository
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__ = MagicMock(return_value=iter([]))
        mock_collection.find.return_value = mock_cursor

        repo.search_articles("Manchester United transfer")

        find_call = mock_collection.find.call_args
        query = find_call[0][0]
        assert "$text" in query

    def test_is_healthy(self, repository):
        repo, _ = repository
        assert repo.is_healthy() is True
