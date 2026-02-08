"""Tests for ContentProcessorOrchestrator."""
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.interfaces.llm_provider import InferenceOutput
from src.objects.content.raw_content import RawContent
from src.services.content_processor.content_processor_orchestrator import ContentProcessorOrchestrator


class TestContentProcessorOrchestrator:
    @pytest.fixture
    def orchestrator(self, mock_content_repository, mock_llm_factory):
        return ContentProcessorOrchestrator(
            content_repository=mock_content_repository,
            llm_factory=mock_llm_factory,
            processing_model="Gemini-Flash",
            api_key="test-key",
        )

    def test_handle_success(self, orchestrator, mock_content_repository, mock_llm_factory, sample_raw_content):
        llm_response = json.dumps({
            "summary": "Man United signed a striker",
            "entities": [{"name": "Manchester United", "type": "team", "normalized": "manchester_united"}],
            "categories": ["football", "transfer"],
            "sentiment": "positive",
        })
        mock_provider = mock_llm_factory.create_provider.return_value
        mock_provider.generate.return_value = InferenceOutput(
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
        assert len(stored_article.entities) == 1
        assert stored_article.entities[0].normalized == "manchester_united"

    def test_handle_llm_failure(self, orchestrator, mock_llm_factory, sample_raw_content):
        mock_provider = mock_llm_factory.create_provider.return_value
        mock_provider.generate.side_effect = Exception("LLM error")

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
