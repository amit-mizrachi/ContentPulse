"""Unit tests for external_inference_service module."""
from unittest.mock import MagicMock, patch
import json


class TestInferenceManager:
    """Tests for InferenceOrchestrator using dependency injection."""

    @patch('src.services.inference.inference_orchestrator.Logger')
    def test_handle_valid_message(
        self, mock_orchestrator_logger,
        sample_gateway_request, sample_inference_result
    ):
        """Test handling a valid inference message."""
        # Create mock dependencies
        mock_state_repo = MagicMock()
        mock_message_publisher = MagicMock()
        mock_llm_factory = MagicMock()

        from src.services.inference.inference_orchestrator import InferenceOrchestrator
        from src.interfaces.llm_provider import InferenceOutput

        # Setup LLM factory mock - now uses generate() returning InferenceOutput
        mock_provider = MagicMock()
        mock_provider.generate.return_value = InferenceOutput(**sample_inference_result)
        mock_llm_factory.create_provider.return_value = mock_provider
        mock_llm_factory.resolve_model_name.return_value = "gpt-4o-mini"

        # Inject mocks via constructor
        orchestrator = InferenceOrchestrator(
            state_repository=mock_state_repo,
            message_publisher=mock_message_publisher,
            llm_factory=mock_llm_factory,
            judge_topic="judge"
        )

        raw_message = {
            "request_id": "test-123",
            "topic_name": "inference",
            "gateway_request": sample_gateway_request
        }

        result = orchestrator.handle(raw_message)

        assert result is True

        # Verify state repository was updated
        assert mock_state_repo.update.call_count >= 2

        # Verify message publisher was called
        mock_message_publisher.publish.assert_called_once()

    @patch('src.services.inference.inference_orchestrator.Logger')
    def test_handle_openai_error(
        self, mock_orchestrator_logger,
        sample_gateway_request
    ):
        """Test handling when LLM provider returns an error."""
        mock_state_repo = MagicMock()
        mock_message_publisher = MagicMock()
        mock_llm_factory = MagicMock()

        from src.services.inference.inference_orchestrator import InferenceOrchestrator

        # Setup LLM factory to raise error
        mock_provider = MagicMock()
        mock_provider.generate.side_effect = Exception("API rate limit exceeded")
        mock_llm_factory.create_provider.return_value = mock_provider
        mock_llm_factory.resolve_model_name.return_value = "gpt-4o-mini"

        orchestrator = InferenceOrchestrator(
            state_repository=mock_state_repo,
            message_publisher=mock_message_publisher,
            llm_factory=mock_llm_factory,
            judge_topic="judge"
        )

        raw_message = {
            "request_id": "test-123",
            "topic_name": "inference",
            "gateway_request": sample_gateway_request
        }

        result = orchestrator.handle(raw_message)

        assert result is False

        # Verify state repo was updated with Failed stage
        last_update_call = mock_state_repo.update.call_args_list[-1]
        updates = last_update_call[0][1]
        assert updates["stage"] == "Failed"
        assert "error_message" in updates

    @patch('src.services.inference.inference_orchestrator.Logger')
    def test_model_mapping(
        self, mock_orchestrator_logger,
        sample_inference_result
    ):
        """Test that model name is properly resolved by factory."""
        mock_state_repo = MagicMock()
        mock_message_publisher = MagicMock()
        mock_llm_factory = MagicMock()

        from src.services.inference.inference_orchestrator import InferenceOrchestrator
        from src.interfaces.llm_provider import InferenceOutput, InferenceConfig

        mock_provider = MagicMock()
        mock_provider.generate.return_value = InferenceOutput(**sample_inference_result)
        mock_llm_factory.create_provider.return_value = mock_provider
        mock_llm_factory.resolve_model_name.return_value = "gpt-4"

        orchestrator = InferenceOrchestrator(
            state_repository=mock_state_repo,
            message_publisher=mock_message_publisher,
            llm_factory=mock_llm_factory,
            judge_topic="judge"
        )

        raw_message = {
            "request_id": "test-123",
            "topic_name": "inference",
            "gateway_request": {
                "prompt": "test",
                "target_model": {"name": "GPT-4"},
                "api_key": "sk-test",
                "judge_model": {"name": "qwen2.5", "version": "latest"}
            }
        }

        orchestrator.handle(raw_message)

        # Verify factory was called to create provider and resolve model name
        mock_llm_factory.create_provider.assert_called_once()
        mock_llm_factory.resolve_model_name.assert_called_once_with("GPT-4")

        # Verify generate was called with correct InferenceConfig
        call_args = mock_provider.generate.call_args
        assert call_args[1]["config"].model == "gpt-4"

    @patch('src.services.inference.inference_orchestrator.Logger')
    def test_publishes_judge_message(
        self, mock_orchestrator_logger,
        sample_gateway_request, sample_inference_result
    ):
        """Test that judge message is published after inference."""
        mock_state_repo = MagicMock()
        mock_message_publisher = MagicMock()
        mock_llm_factory = MagicMock()

        from src.services.inference.inference_orchestrator import InferenceOrchestrator
        from src.interfaces.llm_provider import InferenceOutput

        mock_provider = MagicMock()
        mock_provider.generate.return_value = InferenceOutput(**sample_inference_result)
        mock_llm_factory.create_provider.return_value = mock_provider
        mock_llm_factory.resolve_model_name.return_value = "gpt-4o-mini"

        orchestrator = InferenceOrchestrator(
            state_repository=mock_state_repo,
            message_publisher=mock_message_publisher,
            llm_factory=mock_llm_factory,
            judge_topic="judge"
        )

        raw_message = {
            "request_id": "test-123",
            "topic_name": "inference",
            "gateway_request": sample_gateway_request
        }

        orchestrator.handle(raw_message)

        # Verify message publisher publish was called with judge topic
        publish_call = mock_message_publisher.publish.call_args
        topic_arn = publish_call[0][0]
        message = json.loads(publish_call[0][1])

        assert topic_arn == "judge"
        assert message["request_id"] == "test-123"
        assert "inference_result" in message

    @patch('src.services.inference.inference_orchestrator.Logger')
    def test_updates_state_with_inference_result(
        self, mock_orchestrator_logger,
        sample_gateway_request, sample_inference_result
    ):
        """Test that state repository is updated with inference result."""
        mock_state_repo = MagicMock()
        mock_message_publisher = MagicMock()
        mock_llm_factory = MagicMock()

        from src.services.inference.inference_orchestrator import InferenceOrchestrator
        from src.interfaces.llm_provider import InferenceOutput

        mock_provider = MagicMock()
        mock_provider.generate.return_value = InferenceOutput(**sample_inference_result)
        mock_llm_factory.create_provider.return_value = mock_provider
        mock_llm_factory.resolve_model_name.return_value = "gpt-4o-mini"

        orchestrator = InferenceOrchestrator(
            state_repository=mock_state_repo,
            message_publisher=mock_message_publisher,
            llm_factory=mock_llm_factory,
            judge_topic="judge"
        )

        raw_message = {
            "request_id": "test-123",
            "topic_name": "inference",
            "gateway_request": sample_gateway_request
        }

        orchestrator.handle(raw_message)

        # Find the call that updated inference_result
        update_calls = mock_state_repo.update.call_args_list
        inference_result_update = None
        for call in update_calls:
            updates = call[0][1]
            if "inference_result" in updates:
                inference_result_update = updates
                break

        assert inference_result_update is not None
        assert inference_result_update["inference_result"]["response"] == sample_inference_result["response"]
