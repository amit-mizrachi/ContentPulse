"""Integration tests for request state transitions.

Tests verify that request stages progress correctly through the lifecycle:
Gateway -> Inference -> Judge -> Completed (or Failed)
"""
from unittest.mock import MagicMock, patch


class TestRequestStageProgression:
    """Tests for request stage progression through Redis."""

    @patch('src.utils.services.clients.redis_client.httpx.Client')
    @patch('src.utils.services.clients.redis_client.get_config_service')
    def test_stages_progress_in_order(self, mock_get_config, mock_httpx_client):
        """Request stages should progress in correct order."""
        mock_appconfig = MagicMock()
        mock_get_config.return_value = mock_appconfig
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "services.redis.host": "localhost",
            "services.redis.port": 8001
        }.get(key, default)

        stage_updates = []

        def track_patch(url, json):
            if "stage" in json:
                stage_updates.append(json["stage"])
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "request_id": "test-123",
                "gateway_request": {
                    "prompt": "test",
                    "target_model": {"name": "ChatGPT"},
                    "api_key": "sk-key",
                    "judge_model": {"name": "qwen2.5", "version": "latest"}
                },
                "stage": json.get("stage", "Gateway"),
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
            mock_response.raise_for_status = MagicMock()
            return mock_response

        mock_httpx_client.return_value.patch.side_effect = track_patch

        from src.utils.services.clients.redis_client import RedisClient, get_state_repository
        get_state_repository.cache_clear()

        client = RedisClient()

        client.update_request("test-123", {"stage": "Inference"})
        client.update_request("test-123", {"stage": "Judge"})
        client.update_request("test-123", {"stage": "Completed"})

        assert stage_updates == ["Inference", "Judge", "Completed"]

    @patch('src.utils.services.clients.redis_client.httpx.Client')
    @patch('src.utils.services.clients.redis_client.get_config_service')
    def test_failed_stage_can_occur_at_inference(self, mock_get_config, mock_httpx_client):
        """Request can transition to Failed during inference."""
        mock_appconfig = MagicMock()
        mock_get_config.return_value = mock_appconfig
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "services.redis.host": "localhost",
            "services.redis.port": 8001
        }.get(key, default)

        stage_updates = []

        def track_patch(url, json):
            if "stage" in json:
                stage_updates.append(json["stage"])
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "request_id": "test-123",
                "gateway_request": {
                    "prompt": "test",
                    "target_model": {"name": "ChatGPT"},
                    "api_key": "sk-key",
                    "judge_model": {"name": "qwen2.5", "version": "latest"}
                },
                "stage": json.get("stage", "Gateway"),
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
            mock_response.raise_for_status = MagicMock()
            return mock_response

        mock_httpx_client.return_value.patch.side_effect = track_patch

        from src.utils.services.clients.redis_client import RedisClient, get_state_repository
        get_state_repository.cache_clear()

        client = RedisClient()

        client.update_request("test-123", {"stage": "Inference"})
        client.update_request("test-123", {"stage": "Failed", "error_message": "API error"})

        assert stage_updates == ["Inference", "Failed"]

    @patch('src.utils.services.clients.redis_client.httpx.Client')
    @patch('src.utils.services.clients.redis_client.get_config_service')
    def test_failed_stage_can_occur_at_judge(self, mock_get_config, mock_httpx_client):
        """Request can transition to Failed during judging."""
        mock_appconfig = MagicMock()
        mock_get_config.return_value = mock_appconfig
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "services.redis.host": "localhost",
            "services.redis.port": 8001
        }.get(key, default)

        stage_updates = []

        def track_patch(url, json):
            if "stage" in json:
                stage_updates.append(json["stage"])
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "request_id": "test-123",
                "gateway_request": {
                    "prompt": "test",
                    "target_model": {"name": "ChatGPT"},
                    "api_key": "sk-key",
                    "judge_model": {"name": "qwen2.5", "version": "latest"}
                },
                "stage": json.get("stage", "Gateway"),
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
            mock_response.raise_for_status = MagicMock()
            return mock_response

        mock_httpx_client.return_value.patch.side_effect = track_patch

        from src.utils.services.clients.redis_client import RedisClient, get_state_repository
        get_state_repository.cache_clear()

        client = RedisClient()

        client.update_request("test-123", {"stage": "Inference"})
        client.update_request("test-123", {"stage": "Judge"})
        client.update_request("test-123", {"stage": "Failed", "error_message": "Judge error"})

        assert stage_updates == ["Inference", "Judge", "Failed"]


class TestErrorStateHandling:
    """Tests for error state handling in request lifecycle."""

    @patch('src.services.inference.inference_orchestrator.Logger')
    def test_inference_error_sets_failed_stage(
        self,
        mock_orchestrator_logger,
        sample_gateway_request
    ):
        """Inference error should set request to Failed stage."""
        captured_updates = []

        # Create mock dependencies using DI
        mock_state_repo = MagicMock()

        def capture_update(request_id, updates):
            captured_updates.append(updates.copy())
            return MagicMock()

        mock_state_repo.update.side_effect = capture_update

        mock_message_publisher = MagicMock()

        mock_llm_factory = MagicMock()
        mock_provider = MagicMock()
        mock_provider.generate.side_effect = Exception("Rate limit exceeded")
        mock_llm_factory.create_provider.return_value = mock_provider
        mock_llm_factory.resolve_model_name.return_value = "gpt-4o-mini"

        from src.services.inference.inference_orchestrator import InferenceOrchestrator

        orchestrator = InferenceOrchestrator(
            state_repository=mock_state_repo,
            message_publisher=mock_message_publisher,
            llm_factory=mock_llm_factory,
            judge_topic="judge"
        )

        message = {
            "request_id": "test-123",
            "topic_name": "inference",
            "gateway_request": sample_gateway_request
        }

        result = orchestrator.handle(message)

        assert result is False

        failed_update = next(
            (u for u in captured_updates if u.get("stage") == "Failed"),
            None
        )
        assert failed_update is not None
        assert "error_message" in failed_update
        assert "Rate limit" in failed_update["error_message"]

    @patch('src.services.judge.judge_orchestrator.Logger')
    def test_judge_error_sets_failed_stage_and_persists(
        self,
        mock_orchestrator_logger,
        sample_gateway_request,
        sample_inference_result
    ):
        """Judge error should set Failed stage and persist failure record."""
        from src.objects.enums.request_stage import RequestStage

        captured_updates = []

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

        def capture_update(request_id, updates):
            captured_updates.append(updates.copy())
            return MagicMock()

        mock_state_repo.update.side_effect = capture_update

        mock_persistence_gateway = MagicMock()
        mock_judge_gateway = MagicMock()
        mock_judge_gateway.judge.side_effect = Exception("Judge inference failed")

        from src.services.judge.judge_orchestrator import JudgeOrchestrator

        orchestrator = JudgeOrchestrator(
            state_repository=mock_state_repo,
            persistence_gateway=mock_persistence_gateway,
            judge_gateway=mock_judge_gateway
        )

        message = {
            "request_id": "test-123",
            "topic_name": "judge",
            "gateway_request": sample_gateway_request,
            "inference_result": sample_inference_result
        }

        result = orchestrator.handle(message)

        assert result is False

        failed_update = next(
            (u for u in captured_updates if u.get("stage") == "Failed"),
            None
        )
        assert failed_update is not None

        mock_persistence_gateway.create_history.assert_called()
        history_data = mock_persistence_gateway.create_history.call_args[0][0]
        assert history_data["status"] == "Failed"
