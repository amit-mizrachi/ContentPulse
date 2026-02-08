"""Tests for ContentProcessorOrchestrator."""
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.shared.objects.inference.inference_result import InferenceResult
from src.shared.objects.content.raw_article import RawArticle
from src.services.content_processor.content_processor_orchestrator import ContentProcessorOrchestrator


class TestContentProcessorOrchestrator:
    @pytest.fixture
    def orchestrator(self, mock_content_repository, mock_llm_provider):
        return ContentProcessorOrchestrator(
            content_repository=mock_content_repository,
            llm_provider=mock_llm_provider,
            model="gemini-2.0-flash",
        )

    def test_handle_success(self, orchestrator, mock_content_repository, mock_llm_provider, sample_raw_content):
        llm_response = json.dumps({
            "summary": "Man United signed a striker",
            "entities": [
                {"name": "Manchester United", "type": "team", "normalized": "manchester_united"},
                {"name": "Premier League", "type": "league", "normalized": "premier_league"},
                {"name": "Football", "type": "sport", "normalized": "football"},
            ],
            "categories": ["transfer"],
            "sentiment": "positive",
        })
        mock_llm_provider.run_inference.return_value = InferenceResult(
            response=llm_response, model="gemini-2.0-flash",
            prompt_tokens=100, completion_tokens=50, total_tokens=150, latency_ms=500,
        )

        message_data = {
            "request_id": "test-1",
            "topic_name": "content-raw",
            "raw_content": sample_raw_content.model_dump(mode="json"),
        }

        result = orchestrator.handle(message_data)
        assert result is True
        mock_content_repository.store_article.assert_called_once()

        stored_article = mock_content_repository.store_article.call_args[0][0]
        assert stored_article.summary == "Man United signed a striker"
        assert stored_article.sentiment == "positive"
        assert len(stored_article.entities) == 3
        assert stored_article.entities[0].normalized == "manchester_united"
        assert stored_article.entities[1].type == "league"
        assert stored_article.entities[2].type == "sport"

    def test_handle_llm_failure(self, orchestrator, mock_llm_provider, sample_raw_content):
        mock_llm_provider.run_inference.side_effect = Exception("LLM error")

        message_data = {
            "request_id": "test-2",
            "topic_name": "content-raw",
            "raw_content": sample_raw_content.model_dump(mode="json"),
        }

        result = orchestrator.handle(message_data)
        assert result is False

    def test_handle_invalid_message(self, orchestrator):
        result = orchestrator.handle({"invalid": "data"})
        assert result is False
