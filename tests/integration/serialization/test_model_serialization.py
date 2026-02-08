"""Integration tests for model serialization round-trips."""
import json
from datetime import datetime, timezone

import pytest

from src.shared.objects.content.raw_article import RawArticle
from src.shared.objects.content.article_entity import ArticleEntity
from src.shared.objects.content.processed_article import ProcessedArticle
from src.shared.objects.requests.processed_request import ProcessedQuery
from src.shared.objects.enums.request_stage import RequestStage
from src.shared.objects.messages.content_message import ContentMessage
from src.shared.objects.messages.query_message import QueryMessage
from src.shared.objects.requests.query_filters import QueryFilters
from src.shared.objects.requests.query_request import QueryRequest
from src.shared.objects.results.query_result import QueryResult
from src.shared.objects.results.source_reference import SourceReference


class TestModelSerializationRoundTrips:
    def test_raw_content_json_roundtrip(self, sample_raw_content):
        json_str = sample_raw_content.model_dump_json()
        data = json.loads(json_str)
        restored = RawArticle.model_validate(data)
        assert restored == sample_raw_content

    def test_processed_article_json_roundtrip(self, sample_processed_article):
        json_str = sample_processed_article.model_dump_json()
        data = json.loads(json_str)
        restored = ProcessedArticle.model_validate(data)
        assert restored.source == sample_processed_article.source
        assert restored.entities[0].normalized == sample_processed_article.entities[0].normalized

    def test_query_request_with_filters_roundtrip(self):
        qr = QueryRequest(
            query="Who scored in the Premier League?",
            filters=QueryFilters(
                sources=["reddit", "espn"],
                categories=["football"],
                date_from=datetime(2024, 1, 1, tzinfo=timezone.utc),
                date_to=datetime(2024, 12, 31, tzinfo=timezone.utc),
            ),
        )
        json_str = qr.model_dump_json()
        restored = QueryRequest.model_validate_json(json_str)
        assert restored.filters.sources == ["reddit", "espn"]

    def test_query_result_roundtrip(self, sample_query_result):
        json_str = sample_query_result.model_dump_json()
        restored = QueryResult.model_validate_json(json_str)
        assert restored.answer == sample_query_result.answer
        assert len(restored.sources) == len(sample_query_result.sources)

    def test_processed_query_full_lifecycle(self, sample_query_request, sample_query_result):
        # Gateway stage
        pq = ProcessedQuery(
            request_id="lifecycle-1",
            query_request=sample_query_request,
            stage=RequestStage.Gateway,
        )
        s1 = pq.model_dump_json()
        r1 = ProcessedQuery.model_validate_json(s1)
        assert r1.stage == RequestStage.Gateway
        assert r1.query_result is None

        # Processing stage
        pq_processing = r1.model_copy(update={"stage": RequestStage.QueryProcessing})
        s2 = pq_processing.model_dump_json()
        r2 = ProcessedQuery.model_validate_json(s2)
        assert r2.stage == RequestStage.QueryProcessing

        # Completed stage
        pq_completed = r2.model_copy(update={
            "stage": RequestStage.Completed,
            "query_result": sample_query_result,
        })
        s3 = pq_completed.model_dump_json()
        r3 = ProcessedQuery.model_validate_json(s3)
        assert r3.stage == RequestStage.Completed
        assert r3.query_result.answer == sample_query_result.answer

    def test_content_message_roundtrip(self, sample_raw_content):
        msg = ContentMessage(request_id="cm-1", raw_content=sample_raw_content)
        json_str = msg.model_dump_json()
        data = json.loads(json_str)
        restored = ContentMessage.model_validate(data)
        assert restored.topic_name == "content-raw"
        assert restored.raw_content.source_id == "abc123"

    def test_query_message_roundtrip(self, sample_query_request):
        msg = QueryMessage(request_id="qm-1", query_request=sample_query_request)
        json_str = msg.model_dump_json()
        data = json.loads(json_str)
        restored = QueryMessage.model_validate(data)
        assert restored.topic_name == "query"
        assert restored.query_request.query == sample_query_request.query
