"""Integration test: Poller → Content Processor → MongoDB flow."""
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.interfaces.llm_provider import InferenceOutput
from src.objects.content.raw_content import RawContent
from src.objects.messages.content_message import ContentMessage
from src.services.content_processor.content_processor_orchestrator import ContentProcessorOrchestrator


class TestContentIngestionFlow:
    def test_content_message_to_stored_article(
        self, mock_content_repository, mock_llm_factory, sample_raw_content,
    ):
        """Test: raw content message → LLM enrichment → stored article."""
        # Simulate what the poller would publish
        message = ContentMessage(
            request_id="ingest-1",
            raw_content=sample_raw_content,
        )
        message_data = json.loads(message.model_dump_json())

        # Setup LLM response
        llm_response = json.dumps({
            "summary": "Manchester United completed a new transfer signing.",
            "entities": [
                {"name": "Manchester United", "type": "team", "normalized": "manchester_united"},
            ],
            "categories": ["football", "premier_league", "transfer"],
            "sentiment": "positive",
        })
        mock_provider = mock_llm_factory.create_provider.return_value
        mock_provider.generate.return_value = InferenceOutput(
            response=llm_response, model="gemini-2.0-flash",
            prompt_tokens=100, completion_tokens=50, total_tokens=150, latency_ms=400,
        )

        # Process
        processor = ContentProcessorOrchestrator(
            content_repository=mock_content_repository,
            llm_factory=mock_llm_factory,
            processing_model="Gemini-Flash",
            api_key="test-key",
        )
        result = processor.handle(message_data)
        assert result is True

        # Verify article stored
        mock_content_repository.store_article.assert_called_once()
        stored = mock_content_repository.store_article.call_args[0][0]
        assert stored.source == "reddit"
        assert stored.source_id == "abc123"
        assert stored.summary == "Manchester United completed a new transfer signing."
        assert stored.sentiment == "positive"
        assert len(stored.entities) == 1
        assert stored.categories == ["football", "premier_league", "transfer"]
