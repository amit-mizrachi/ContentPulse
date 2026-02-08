"""Unit tests for judge_service module."""
from unittest.mock import MagicMock, patch


class TestJudgeManager:
    """Tests for JudgeOrchestrator using dependency injection."""

    @patch('src.services.judge.judge_orchestrator.Logger')
    def test_handle_valid_message(
        self, mock_orchestrator_logger,
        sample_gateway_request, sample_inference_result, sample_judge_result
    ):
        """Test handling a valid judge message."""
        from src.objects.enums.request_stage import RequestStage

        # Create mock dependencies
        mock_state_repo = MagicMock()
        mock_state_repo.get.return_value = {
            "request_id": "test-123",
            "gateway_request": sample_gateway_request,
            "stage": RequestStage.Judge.value,
            "created_at": "2024-01-01T00:00:00"
        }

        mock_persistence_gateway = MagicMock()
        mock_judge_gateway = MagicMock()
        mock_judge_gateway.judge.return_value = sample_judge_result  # Returns Dict, not JudgeResult

        from src.services.judge.judge_orchestrator import JudgeOrchestrator

        # Inject mocks via constructor
        orchestrator = JudgeOrchestrator(
            state_repository=mock_state_repo,
            persistence_gateway=mock_persistence_gateway,
            judge_gateway=mock_judge_gateway
        )

        raw_message = {
            "request_id": "test-123",
            "topic_name": "judge",
            "gateway_request": sample_gateway_request,
            "inference_result": sample_inference_result
        }

        result = orchestrator.handle(raw_message)

        assert result is True

        # Verify state repo was updated with Completed stage
        update_calls = mock_state_repo.update.call_args_list
        completed_update = None
        for call in update_calls:
            updates = call[0][1]
            if updates.get("stage") == "Completed":
                completed_update = updates
                break
        assert completed_update is not None

        # Verify persistence was called to store history
        mock_persistence_gateway.create_history.assert_called_once()

    @patch('src.services.judge.judge_orchestrator.Logger')
    def test_handle_judge_error(
        self, mock_orchestrator_logger,
        sample_gateway_request, sample_inference_result
    ):
        """Test handling when judge inference fails."""
        from src.objects.enums.request_stage import RequestStage

        mock_state_repo = MagicMock()
        # Return state data for archive_request after failure
        mock_state_repo.get.return_value = {
            "request_id": "test-123",
            "gateway_request": sample_gateway_request,
            "stage": RequestStage.Failed.value,
            "inference_result": sample_inference_result,
            "error_message": "Judge inference failed",
            "created_at": "2024-01-01T00:00:00"
        }

        mock_persistence_gateway = MagicMock()
        mock_judge_gateway = MagicMock()
        mock_judge_gateway.judge.side_effect = Exception("Judge inference failed")

        from src.services.judge.judge_orchestrator import JudgeOrchestrator

        orchestrator = JudgeOrchestrator(
            state_repository=mock_state_repo,
            persistence_gateway=mock_persistence_gateway,
            judge_gateway=mock_judge_gateway
        )

        raw_message = {
            "request_id": "test-123",
            "topic_name": "judge",
            "gateway_request": sample_gateway_request,
            "inference_result": sample_inference_result
        }

        result = orchestrator.handle(raw_message)

        assert result is False

        # Verify state repo was updated with Failed stage
        update_calls = mock_state_repo.update.call_args_list
        failed_update = None
        for call in update_calls:
            updates = call[0][1]
            if updates.get("stage") == "Failed":
                failed_update = updates
                break
        assert failed_update is not None
        assert "error_message" in failed_update

        # Verify persistence was still called with Failed status
        mock_persistence_gateway.create_history.assert_called()
        history_data = mock_persistence_gateway.create_history.call_args[0][0]
        assert history_data["status"] == "Failed"

    @patch('src.services.judge.judge_orchestrator.Logger')
    def test_creates_correct_history_data(
        self, mock_orchestrator_logger,
        sample_gateway_request, sample_inference_result, sample_judge_result
    ):
        """Test that history data is correctly formatted."""
        from src.objects.enums.request_stage import RequestStage

        mock_state_repo = MagicMock()
        # Return complete state data for archive
        mock_state_repo.get.return_value = {
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

        from src.services.judge.judge_orchestrator import JudgeOrchestrator

        orchestrator = JudgeOrchestrator(
            state_repository=mock_state_repo,
            persistence_gateway=mock_persistence_gateway,
            judge_gateway=mock_judge_gateway
        )

        raw_message = {
            "request_id": "test-123",
            "topic_name": "judge",
            "gateway_request": sample_gateway_request,
            "inference_result": sample_inference_result
        }

        orchestrator.handle(raw_message)

        # Verify history data structure
        history_data = mock_persistence_gateway.create_history.call_args[0][0]

        assert history_data["request_id"] == "test-123"
        assert history_data["prompt"] == sample_gateway_request["prompt"]
        assert history_data["target_model"] == sample_gateway_request["target_model"]["name"]
        assert "qwen2.5:latest" in history_data["judge_model"]
        assert history_data["inference_response"] == sample_inference_result["response"]
        assert history_data["inference_latency_ms"] == sample_inference_result["latency_ms"]
        assert history_data["inference_tokens"] == sample_inference_result["total_tokens"]
        assert history_data["judge_score"] == sample_judge_result["score"]
        assert history_data["judge_reasoning"] == sample_judge_result["reasoning"]
        assert history_data["status"] == "Completed"

    @patch('src.services.judge.judge_orchestrator.Logger')
    def test_calls_judge_inference_with_correct_params(
        self, mock_orchestrator_logger,
        sample_gateway_request, sample_inference_result, sample_judge_result
    ):
        """Test that judge client is called with correct parameters."""
        from src.objects.enums.request_stage import RequestStage

        mock_state_repo = MagicMock()
        mock_state_repo.get.return_value = {
            "request_id": "test-123",
            "gateway_request": sample_gateway_request,
            "stage": RequestStage.Judge.value,
            "created_at": "2024-01-01T00:00:00"
        }

        mock_persistence_gateway = MagicMock()
        mock_judge_gateway = MagicMock()
        mock_judge_gateway.judge.return_value = sample_judge_result  # Returns Dict

        from src.services.judge.judge_orchestrator import JudgeOrchestrator

        orchestrator = JudgeOrchestrator(
            state_repository=mock_state_repo,
            persistence_gateway=mock_persistence_gateway,
            judge_gateway=mock_judge_gateway
        )

        raw_message = {
            "request_id": "test-123",
            "topic_name": "judge",
            "gateway_request": sample_gateway_request,
            "inference_result": sample_inference_result
        }

        orchestrator.handle(raw_message)

        # Verify judge gateway was called with correct params
        mock_judge_gateway.judge.assert_called_once_with(
            original_prompt=sample_gateway_request["prompt"],
            model_response=sample_inference_result["response"],
            model="qwen2.5:latest"
        )

    @patch('src.services.judge.judge_orchestrator.Logger')
    def test_handles_persistence_failure_on_error_path(
        self, mock_orchestrator_logger,
        sample_gateway_request, sample_inference_result
    ):
        """Test graceful handling when both judge and persistence fail."""
        from src.objects.enums.request_stage import RequestStage

        mock_state_repo = MagicMock()
        mock_state_repo.get.return_value = {
            "request_id": "test-123",
            "gateway_request": sample_gateway_request,
            "stage": RequestStage.Judge.value,
            "created_at": "2024-01-01T00:00:00"
        }

        mock_persistence_gateway = MagicMock()
        mock_persistence_gateway.create_history.side_effect = Exception("DB connection failed")

        mock_judge_gateway = MagicMock()
        mock_judge_gateway.judge.side_effect = Exception("Judge inference failed")

        from src.services.judge.judge_orchestrator import JudgeOrchestrator

        orchestrator = JudgeOrchestrator(
            state_repository=mock_state_repo,
            persistence_gateway=mock_persistence_gateway,
            judge_gateway=mock_judge_gateway
        )

        raw_message = {
            "request_id": "test-123",
            "topic_name": "judge",
            "gateway_request": sample_gateway_request,
            "inference_result": sample_inference_result
        }

        # Should not raise, should return False gracefully
        result = orchestrator.handle(raw_message)

        assert result is False

    @patch('src.services.judge.judge_orchestrator.Logger')
    def test_updates_state_with_judge_result(
        self, mock_orchestrator_logger,
        sample_gateway_request, sample_inference_result, sample_judge_result
    ):
        """Test that state repository is updated with judge result."""
        from src.objects.enums.request_stage import RequestStage

        mock_state_repo = MagicMock()
        mock_state_repo.get.return_value = {
            "request_id": "test-123",
            "gateway_request": sample_gateway_request,
            "stage": RequestStage.Judge.value,
            "created_at": "2024-01-01T00:00:00"
        }

        mock_persistence_gateway = MagicMock()
        mock_judge_gateway = MagicMock()
        mock_judge_gateway.judge.return_value = sample_judge_result  # Returns Dict

        from src.services.judge.judge_orchestrator import JudgeOrchestrator

        orchestrator = JudgeOrchestrator(
            state_repository=mock_state_repo,
            persistence_gateway=mock_persistence_gateway,
            judge_gateway=mock_judge_gateway
        )

        raw_message = {
            "request_id": "test-123",
            "topic_name": "judge",
            "gateway_request": sample_gateway_request,
            "inference_result": sample_inference_result
        }

        orchestrator.handle(raw_message)

        # Find the call that updated judge_result
        update_calls = mock_state_repo.update.call_args_list
        judge_result_update = None
        for call in update_calls:
            updates = call[0][1]
            if "judge_result" in updates:
                judge_result_update = updates
                break

        assert judge_result_update is not None
        assert judge_result_update["judge_result"]["score"] == sample_judge_result["score"]
        assert judge_result_update["stage"] == "Completed"
