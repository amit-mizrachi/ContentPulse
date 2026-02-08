"""Tests for all new Pydantic models serialization."""
from datetime import datetime, timezone

from src.objects.content.raw_content import RawContent
from src.objects.content.processed_article import ProcessedArticle, Entity
from src.objects.requests.processed_request import ProcessedQuery
from src.objects.enums.request_stage import RequestStage
from src.objects.messages.content_message import ContentMessage
from src.objects.messages.query_message import QueryMessage
from src.objects.requests.query_request import QueryRequest, QueryFilters
from src.objects.responses.query_response import QueryResponse
from src.objects.enums.request_status import RequestStatus
from src.objects.results.query_result import QueryResult, SourceReference


class TestRawContent:
    def test_serialization_roundtrip(self, sample_raw_content):
        json_str = sample_raw_content.model_dump_json()
        restored = RawContent.model_validate_json(json_str)
        assert restored.source == "reddit"
        assert restored.source_id == "abc123"
        assert restored.title == "Manchester United signs new striker"

    def test_metadata_default(self):
        rc = RawContent(
            source="espn", source_id="x", source_url="http://espn.com",
            title="Test", content="Test content",
            published_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        assert rc.metadata == {}


class TestProcessedArticle:
    def test_serialization_roundtrip(self, sample_processed_article):
        json_str = sample_processed_article.model_dump_json()
        restored = ProcessedArticle.model_validate_json(json_str)
        assert restored.summary == "Manchester United completed a new striker signing from an Italian club."
        assert len(restored.entities) == 1
        assert restored.entities[0].normalized == "manchester_united"
        assert "football" in restored.categories

    def test_entity_model(self):
        entity = Entity(name="Cristiano Ronaldo", type="person", normalized="cristiano_ronaldo")
        data = entity.model_dump()
        assert data["type"] == "person"


class TestQueryRequest:
    def test_simple_query(self):
        qr = QueryRequest(query="What happened in the Premier League today?")
        assert qr.filters is None

    def test_with_filters(self, sample_query_request):
        json_str = sample_query_request.model_dump_json()
        restored = QueryRequest.model_validate_json(json_str)
        assert restored.query == "What are the latest Manchester United transfer news?"
        assert restored.filters.categories == ["football"]


class TestQueryResult:
    def test_serialization_roundtrip(self, sample_query_result):
        json_str = sample_query_result.model_dump_json()
        restored = QueryResult.model_validate_json(json_str)
        assert restored.answer == "Manchester United have signed a new striker from Serie A."
        assert len(restored.sources) == 1
        assert restored.model == "gemini-2.0-flash"


class TestQueryResponse:
    def test_serialization(self):
        resp = QueryResponse(request_id="test-123", status=RequestStatus.Accepted)
        data = resp.model_dump()
        assert data["status"] == "Accepted"


class TestProcessedQuery:
    def test_serialization_roundtrip(self, sample_query_request, sample_query_result):
        pq = ProcessedQuery(
            request_id="req-123",
            query_request=sample_query_request,
            stage=RequestStage.Completed,
            query_result=sample_query_result,
        )
        json_str = pq.model_dump_json()
        restored = ProcessedQuery.model_validate_json(json_str)
        assert restored.request_id == "req-123"
        assert restored.stage == RequestStage.Completed
        assert restored.query_result.answer == sample_query_result.answer

    def test_initial_state(self, sample_query_request):
        pq = ProcessedQuery(
            request_id="req-456",
            query_request=sample_query_request,
            stage=RequestStage.Gateway,
        )
        assert pq.query_result is None
        assert pq.error_message is None


class TestContentMessage:
    def test_serialization(self, sample_raw_content):
        msg = ContentMessage(request_id="msg-1", raw_content=sample_raw_content)
        assert msg.topic_name == "content-raw"
        json_str = msg.model_dump_json()
        restored = ContentMessage.model_validate_json(json_str)
        assert restored.raw_content.source == "reddit"


class TestQueryMessage:
    def test_serialization(self, sample_query_request):
        msg = QueryMessage(request_id="msg-2", query_request=sample_query_request)
        assert msg.topic_name == "query"
        json_str = msg.model_dump_json()
        restored = QueryMessage.model_validate_json(json_str)
        assert restored.query_request.query == sample_query_request.query


class TestRequestStage:
    def test_stages_exist(self):
        assert RequestStage.Gateway.value == "Gateway"
        assert RequestStage.QueryProcessing.value == "QueryProcessing"
        assert RequestStage.Completed.value == "Completed"
        assert RequestStage.Failed.value == "Failed"

    def test_no_old_stages(self):
        stage_names = [s.name for s in RequestStage]
        assert "Inference" not in stage_names
        assert "Judge" not in stage_names
