"""Tests for ArticleRepository (mocked MongoDB)."""
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.objects.content.processed_article import ProcessedArticle, Entity
from src.services.mongodb.article_repository import ArticleRepository


class TestArticleRepository:
    @pytest.fixture
    def mock_provider(self):
        provider = MagicMock()
        provider.articles_collection = MagicMock()
        provider.is_healthy.return_value = True
        return provider

    @pytest.fixture
    def repository(self, mock_provider):
        return ArticleRepository(provider=mock_provider)

    def test_store_article(self, repository, mock_provider, sample_processed_article):
        repository.store_article(sample_processed_article)

        mock_provider.articles_collection.update_one.assert_called_once()
        call_args = mock_provider.articles_collection.update_one.call_args
        assert call_args[0][0] == {"source": "reddit", "source_id": "abc123"}

    def test_article_exists_true(self, repository, mock_provider):
        mock_provider.articles_collection.count_documents.return_value = 1
        assert repository.article_exists("reddit", "abc123") is True

    def test_article_exists_false(self, repository, mock_provider):
        mock_provider.articles_collection.count_documents.return_value = 0
        assert repository.article_exists("reddit", "xyz") is False

    def test_query_articles_with_entities(self, repository, mock_provider):
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__ = MagicMock(return_value=iter([]))
        mock_provider.articles_collection.find.return_value = mock_cursor

        repository.query_articles(entities=["manchester_united"])

        find_call = mock_provider.articles_collection.find.call_args
        query = find_call[0][0]
        assert "entities.normalized" in query
        assert query["entities.normalized"] == {"$in": ["manchester_united"]}

    def test_search_articles(self, repository, mock_provider):
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__ = MagicMock(return_value=iter([]))
        mock_provider.articles_collection.find.return_value = mock_cursor

        repository.search_articles("Manchester United transfer")

        find_call = mock_provider.articles_collection.find.call_args
        query = find_call[0][0]
        assert "$text" in query

    def test_is_healthy(self, repository, mock_provider):
        assert repository.is_healthy() is True
        mock_provider.is_healthy.return_value = False
        assert repository.is_healthy() is False
