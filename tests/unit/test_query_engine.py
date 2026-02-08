"""Tests for QueryEngineOrchestrator."""
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, call

import pytest

from src.objects.inference.inference_output import InferenceOutput
from src.objects.enums.request_stage import RequestStage
from src.services.query_engine.query_engine_orchestrator import QueryEngineOrchestrator


class TestQueryEngineOrchestrator:
    @pytest.fixture
    def orchestrator(self, mock_state_repository, mock_content_repository, mock_llm_provider):
        return QueryEngineOrchestrator(
            state_repository=mock_state_repository,
            content_repository=mock_content_repository,
            llm_provider=mock_llm_provider,
            model="gemini-2.0-flash",
        )

    def test_handle_success(self, orchestrator, mock_state_repository, mock_content_repository, mock_llm_provider, sample_query_request):
        # Setup: intent parsing response
        intent_response = json.dumps({
            "entities": ["manchester_united"],
            "categories": ["transfer"],
            "entity_type": None,
            "date_context": "recent",
            "search_terms": "Manchester United transfer",
        })
        # Setup: synthesis response
        synthesis_response = "Manchester United have made several transfer moves recently."

        mock_llm_provider.run_inference.side_effect = [
            InferenceOutput(response=intent_response, model="gemini-2.0-flash",
                          prompt_tokens=50, completion_tokens=30, total_tokens=80, latency_ms=300),
            InferenceOutput(response=synthesis_response, model="gemini-2.0-flash",
                          prompt_tokens=200, completion_tokens=100, total_tokens=300, latency_ms=800),
        ]

        # Setup: articles from MongoDB
        mock_content_repository.query_articles.return_value = [
            {
                "title": "Man United Transfer News",
                "source": "reddit",
                "source_url": "https://reddit.com/r/soccer/abc",
                "summary": "Transfer update for Man United",
                "published_at": datetime(2024, 6, 15, tzinfo=timezone.utc).isoformat(),
            }
        ]

        message_data = {
            "request_id": "query-1",
            "topic_name": "query",
            "query_request": sample_query_request.model_dump(mode="json"),
        }

        result = orchestrator.handle(message_data)
        assert result is True

        # Verify stage transitions
        update_calls = mock_state_repository.update.call_args_list
        assert update_calls[0] == call("query-1", {"stage": "QueryProcessing"})

        # Final update should be Completed with query_result
        final_update = update_calls[-1][0][1]
        assert final_update["stage"] == "Completed"
        assert "query_result" in final_update

    def test_handle_failure_updates_state(self, orchestrator, mock_state_repository, mock_llm_provider, sample_query_request):
        mock_llm_provider.run_inference.side_effect = Exception("LLM unavailable")

        message_data = {
            "request_id": "query-2",
            "topic_name": "query",
            "query_request": sample_query_request.model_dump(mode="json"),
        }

        result = orchestrator.handle(message_data)
        assert result is False

        # Verify failure state
        update_calls = mock_state_repository.update.call_args_list
        failed_update = update_calls[-1][0][1]
        assert failed_update["stage"] == "Failed"
        assert "error_message" in failed_update

    def test_handle_no_articles_returns_fallback(self, orchestrator, mock_content_repository, mock_llm_provider, sample_query_request):
        intent_response = json.dumps({
            "entities": ["obscure_team"],
            "categories": [],
            "entity_type": None,
            "date_context": None,
            "search_terms": "obscure team news",
        })

        mock_llm_provider.run_inference.side_effect = [
            InferenceOutput(response=intent_response, model="gemini-2.0-flash",
                          prompt_tokens=50, completion_tokens=30, total_tokens=80, latency_ms=300),
        ]

        mock_content_repository.query_articles.return_value = []
        mock_content_repository.search_articles.return_value = []

        message_data = {
            "request_id": "query-3",
            "topic_name": "query",
            "query_request": sample_query_request.model_dump(mode="json"),
        }

        result = orchestrator.handle(message_data)
        assert result is True
