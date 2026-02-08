"""Integration test: Gateway → Query Engine → Result flow."""
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.shared.objects.inference.inference_result import InferenceResult
from src.shared.objects.requests.processed_request import ProcessedQuery
from src.shared.objects.enums.request_stage import RequestStage
from src.shared.objects.enums.request_status import RequestStatus
from src.shared.objects.requests.query_request import QueryRequest
from src.services.gateway.query_submission_service import QuerySubmissionService
from src.services.query_engine.query_engine_orchestrator import QueryEngineOrchestrator


class TestQueryFlow:
    def test_end_to_end_query_flow(
        self, mock_state_repository, mock_content_repository,
        mock_message_publisher, mock_llm_provider, sample_query_request,
    ):
        """Test: submit query at gateway → process in query engine → result stored in state."""
        # Phase 1: Submit query via gateway
        gateway_service = QuerySubmissionService(
            state_repository=mock_state_repository,
            message_publisher=mock_message_publisher,
            query_topic="query",
        )
        response = gateway_service.submit_query(sample_query_request)
        assert response.status == RequestStatus.Accepted
        request_id = response.request_id

        # Capture what was published to Kafka
        publish_call = mock_message_publisher.publish.call_args
        published_message = json.loads(publish_call[0][1])

        # Phase 2: Process query in query engine
        intent_response = json.dumps({
            "entities": ["manchester_united"],
            "categories": ["football"],
            "date_context": "recent",
            "search_terms": "Manchester United transfer",
        })
        synthesis_response = "Manchester United have been active in the transfer window."

        mock_llm_provider.run_inference.side_effect = [
            InferenceResult(response=intent_response, model="gemini-2.0-flash",
                          prompt_tokens=50, completion_tokens=30, total_tokens=80, latency_ms=200),
            InferenceResult(response=synthesis_response, model="gemini-2.0-flash",
                          prompt_tokens=200, completion_tokens=80, total_tokens=280, latency_ms=600),
        ]
        mock_content_repository.query_articles.return_value = [
            {"title": "Transfer News", "source": "reddit", "source_url": "http://r.com",
             "summary": "Transfer news summary",
             "published_at": datetime(2024, 6, 1, tzinfo=timezone.utc).isoformat()},
        ]

        engine = QueryEngineOrchestrator(
            state_repository=mock_state_repository,
            content_repository=mock_content_repository,
            llm_provider=mock_llm_provider,
            model="gemini-2.0-flash",
        )
        result = engine.handle(published_message)
        assert result is True

        # Verify final state update
        final_update = mock_state_repository.update.call_args_list[-1][0][1]
        assert final_update["stage"] == "Completed"
        assert "query_result" in final_update
        assert final_update["query_result"]["answer"] == synthesis_response
