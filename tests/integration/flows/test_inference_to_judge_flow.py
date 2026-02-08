"""Integration tests for Inference to Judge service flow.

Tests verify that:
- Inference results are properly passed to Judge service
- Judge messages contain all required data
- The complete flow from inference to persistence works correctly
"""
import json
from unittest.mock import MagicMock, patch


class TestInferenceToJudgeHandoff:
    """Tests for message handoff between inference and judge services."""

    @patch('src.services.judge.judge_orchestrator.Logger')
    @patch('src.services.inference.inference_orchestrator.Logger')
    def test_inference_result_flows_to_judge(
        self,
        mock_inf_logger,
        mock_judge_logger,
        sample_gateway_request,
        sample_inference_result,
        sample_judge_result
    ):
        """Inference result should properly flow to judge service."""
        from src.objects.enums.request_stage import RequestStage
        from src.interfaces.llm_provider import InferenceOutput

        captured_judge_message = {}

        def capture_sns_publish(topic_name, message):
            captured_judge_message["topic_name"] = topic_name
            captured_judge_message["message"] = json.loads(message)
            return True

        # Create mock dependencies for InferenceOrchestrator (using DI)
        mock_inf_state_repo = MagicMock()
        mock_message_publisher = MagicMock()
        mock_message_publisher.publish.side_effect = capture_sns_publish

        mock_llm_factory = MagicMock()
        mock_provider = MagicMock()
        mock_provider.generate.return_value = InferenceOutput(**sample_inference_result)
        mock_llm_factory.create_provider.return_value = mock_provider
        mock_llm_factory.resolve_model_name.return_value = "gpt-4o-mini"

        # Create mock dependencies for JudgeOrchestrator (using DI)
        mock_judge_state_repo = MagicMock()
        mock_judge_state_repo.get.return_value = {
            "request_id": "test-123",
            "gateway_request": sample_gateway_request,
            "stage": RequestStage.Completed.value,
            "inference_result": sample_inference_result,
            "judge_result": sample_judge_result,
            "created_at": "2024-01-01T00:00:00"
        }

        mock_persistence_gateway = MagicMock()
        mock_judge_gateway = MagicMock()
        mock_judge_gateway.judge.return_value = sample_judge_result  # Returns Dict

        from src.services.inference.inference_orchestrator import InferenceOrchestrator
        from src.services.judge.judge_orchestrator import JudgeOrchestrator

        inference_orchestrator = InferenceOrchestrator(
            state_repository=mock_inf_state_repo,
            message_publisher=mock_message_publisher,
            llm_factory=mock_llm_factory,
            judge_topic="judge"
        )

        inference_message = {
            "request_id": "test-123",
            "topic_name": "inference",
            "gateway_request": sample_gateway_request
        }

        inference_result = inference_orchestrator.handle(inference_message)
        assert inference_result is True

        assert captured_judge_message["topic_name"] == "judge"
        assert captured_judge_message["message"]["topic_name"] == "judge"
        assert "inference_result" in captured_judge_message["message"]

        # Use DI-based JudgeOrchestrator
        judge_orchestrator = JudgeOrchestrator(
            state_repository=mock_judge_state_repo,
            persistence_gateway=mock_persistence_gateway,
            judge_gateway=mock_judge_gateway
        )
        judge_result = judge_orchestrator.handle(captured_judge_message["message"])
        assert judge_result is True

        mock_persistence_gateway.create_history.assert_called_once()
        history_data = mock_persistence_gateway.create_history.call_args[0][0]
        assert history_data["status"] == "Completed"
        assert history_data["judge_score"] == sample_judge_result["score"]


class TestJudgeMessageContent:
    """Tests for judge message content validation."""

    @patch('src.services.inference.inference_orchestrator.Logger')
    def test_judge_message_contains_inference_result(
        self,
        mock_orchestrator_logger,
        sample_gateway_request,
        sample_inference_result
    ):
        """Judge message should contain complete inference result."""
        from src.interfaces.llm_provider import InferenceOutput

        captured_message = {}

        def capture_publish(topic_name, message):
            captured_message["data"] = json.loads(message)
            return True

        # Create mock dependencies using DI
        mock_state_repo = MagicMock()
        mock_message_publisher = MagicMock()
        mock_message_publisher.publish.side_effect = capture_publish

        mock_llm_factory = MagicMock()
        mock_provider = MagicMock()
        mock_provider.generate.return_value = InferenceOutput(**sample_inference_result)
        mock_llm_factory.create_provider.return_value = mock_provider
        mock_llm_factory.resolve_model_name.return_value = "gpt-4o-mini"

        from src.services.inference.inference_orchestrator import InferenceOrchestrator

        orchestrator = InferenceOrchestrator(
            state_repository=mock_state_repo,
            message_publisher=mock_message_publisher,
            llm_factory=mock_llm_factory,
            judge_topic="judge"
        )

        inference_message = {
            "request_id": "test-123",
            "topic_name": "inference",
            "gateway_request": sample_gateway_request
        }

        orchestrator.handle(inference_message)

        judge_message = captured_message["data"]
        assert judge_message["inference_result"]["response"] == sample_inference_result["response"]
        assert judge_message["inference_result"]["model"] == sample_inference_result["model"]
        assert judge_message["inference_result"]["latency_ms"] == sample_inference_result["latency_ms"]

    @patch('src.services.inference.inference_orchestrator.Logger')
    def test_judge_message_preserves_original_request(
        self,
        mock_orchestrator_logger,
        sample_gateway_request,
        sample_inference_result
    ):
        """Judge message should preserve original gateway request."""
        from src.interfaces.llm_provider import InferenceOutput

        captured_message = {}

        def capture_publish(topic_name, message):
            captured_message["data"] = json.loads(message)
            return True

        # Create mock dependencies using DI
        mock_state_repo = MagicMock()
        mock_message_publisher = MagicMock()
        mock_message_publisher.publish.side_effect = capture_publish

        mock_llm_factory = MagicMock()
        mock_provider = MagicMock()
        mock_provider.generate.return_value = InferenceOutput(**sample_inference_result)
        mock_llm_factory.create_provider.return_value = mock_provider
        mock_llm_factory.resolve_model_name.return_value = "gpt-4o-mini"

        from src.services.inference.inference_orchestrator import InferenceOrchestrator

        orchestrator = InferenceOrchestrator(
            state_repository=mock_state_repo,
            message_publisher=mock_message_publisher,
            llm_factory=mock_llm_factory,
            judge_topic="judge"
        )

        inference_message = {
            "request_id": "test-123",
            "topic_name": "inference",
            "gateway_request": sample_gateway_request
        }

        orchestrator.handle(inference_message)

        judge_message = captured_message["data"]
        assert judge_message["gateway_request"]["prompt"] == sample_gateway_request["prompt"]
        assert judge_message["gateway_request"]["target_model"]["name"] == sample_gateway_request["target_model"]["name"]
