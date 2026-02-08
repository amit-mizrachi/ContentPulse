"""Shared fixtures for ContentPulse tests."""
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.interfaces.content_repository import ContentRepository
from src.interfaces.llm_provider import LLMProviderFactory, LLMProvider, InferenceConfig, InferenceOutput
from src.interfaces.message_publisher import MessagePublisher
from src.interfaces.state_repository import StateRepository
from src.objects.content.raw_content import RawContent
from src.objects.content.processed_article import ProcessedArticle, Entity
from src.objects.requests.query_request import QueryRequest, QueryFilters
from src.objects.results.query_result import QueryResult, SourceReference


@pytest.fixture(autouse=True)
def mock_logger():
    """Auto-mock Logger everywhere to avoid AppConfig/AWS calls in tests."""
    mock_instance = MagicMock()
    patches = [
        patch("src.services.content_processor.content_processor_orchestrator.Logger", return_value=mock_instance),
        patch("src.services.query_engine.query_engine_orchestrator.Logger", return_value=mock_instance),
        patch("src.services.gateway.query_submission_service.Logger", return_value=mock_instance),
    ]
    for p in patches:
        p.start()
    yield mock_instance
    for p in patches:
        p.stop()


@pytest.fixture
def sample_raw_content():
    return RawContent(
        source="reddit",
        source_id="abc123",
        source_url="https://reddit.com/r/soccer/comments/abc123",
        title="Manchester United signs new striker",
        content="Manchester United have completed the signing of a new striker from Serie A.",
        published_at=datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        metadata={"subreddit": "soccer", "score": 1500},
    )


@pytest.fixture
def sample_processed_article():
    return ProcessedArticle(
        source="reddit",
        source_id="abc123",
        source_url="https://reddit.com/r/soccer/comments/abc123",
        title="Manchester United signs new striker",
        raw_content="Manchester United have completed the signing of a new striker from Serie A.",
        summary="Manchester United completed a new striker signing from an Italian club.",
        entities=[
            Entity(name="Manchester United", type="team", normalized="manchester_united"),
        ],
        categories=["football", "premier_league", "transfer"],
        sentiment="positive",
        published_at=datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        processing_model="gemini-2.0-flash",
    )


@pytest.fixture
def sample_query_request():
    return QueryRequest(
        query="What are the latest Manchester United transfer news?",
        filters=QueryFilters(
            categories=["football"],
        ),
    )


@pytest.fixture
def sample_query_result():
    return QueryResult(
        answer="Manchester United have signed a new striker from Serie A.",
        sources=[
            SourceReference(
                title="Manchester United signs new striker",
                source="reddit",
                source_url="https://reddit.com/r/soccer/comments/abc123",
                published_at=datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
            )
        ],
        metadata={"intent": {"entities": ["manchester_united"]}},
        model="gemini-2.0-flash",
        latency_ms=1234.5,
    )


@pytest.fixture
def mock_state_repository():
    mock = MagicMock(spec=StateRepository)
    mock.create.return_value = {}
    mock.get.return_value = None
    mock.update.return_value = {}
    mock.delete.return_value = True
    mock.is_healthy.return_value = True
    return mock


@pytest.fixture
def mock_content_repository():
    mock = MagicMock(spec=ContentRepository)
    mock.store_article.return_value = {}
    mock.article_exists.return_value = False
    mock.query_articles.return_value = []
    mock.search_articles.return_value = []
    mock.is_healthy.return_value = True
    return mock


@pytest.fixture
def mock_message_publisher():
    mock = MagicMock(spec=MessagePublisher)
    mock.publish.return_value = True
    return mock


@pytest.fixture
def mock_llm_factory():
    mock_provider = MagicMock(spec=LLMProvider)
    mock_provider.generate.return_value = InferenceOutput(
        response='{"summary": "Test summary", "entities": [], "categories": ["test"], "sentiment": "neutral"}',
        model="gemini-2.0-flash",
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        latency_ms=500.0,
    )
    mock_provider.is_healthy.return_value = True

    mock_factory = MagicMock(spec=LLMProviderFactory)
    mock_factory.create_provider.return_value = mock_provider
    mock_factory.resolve_model_name.return_value = "gemini-2.0-flash"
    return mock_factory
