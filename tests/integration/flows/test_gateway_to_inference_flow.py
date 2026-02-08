"""Integration tests for Gateway to Inference service flow.

Tests verify that the gateway service correctly:
- Creates request records in Redis
- Publishes inference messages to SNS
- Returns proper responses to clients
"""
import json
from unittest.mock import MagicMock, patch


class TestGatewaySubmission:
    """Tests for gateway request submission flow."""

    def setup_method(self):
        """Clear singleton instance before each test."""
        from src.services.gateway.request_submission_service import RequestSubmissionService
        RequestSubmissionService._instances = {}

    @patch('src.services.gateway.request_submission_service.get_config_service')
    @patch('src.services.gateway.request_submission_service.get_message_publisher')
    @patch('src.services.gateway.request_submission_service.get_state_repository')
    def test_creates_request_in_redis(
        self,
        mock_get_state_repo,
        mock_get_publisher,
        mock_get_config,
        sample_gateway_request
    ):
        """Gateway should create a request record in Redis before publishing."""
        mock_publisher = MagicMock()
        mock_get_publisher.return_value = mock_publisher

        mock_redis = MagicMock()
        mock_get_state_repo.return_value = mock_redis

        mock_config = MagicMock()
        mock_config.get.return_value = "inference"
        mock_get_config.return_value = mock_config

        from src.services.gateway.request_submission_service import RequestSubmissionService
        from src.objects.requests.gateway_request import GatewayRequest
        from src.objects.enums.request_stage import RequestStage

        manager = RequestSubmissionService()
        request = GatewayRequest(**sample_gateway_request)

        manager.submit_request(request)

        mock_redis.create.assert_called_once()
        created_data = mock_redis.create.call_args[0][1]
        assert created_data["stage"] == RequestStage.Gateway.value

    @patch('src.services.gateway.request_submission_service.get_config_service')
    @patch('src.services.gateway.request_submission_service.get_message_publisher')
    @patch('src.services.gateway.request_submission_service.get_state_repository')
    def test_publishes_to_inference_topic(
        self,
        mock_get_state_repo,
        mock_get_publisher,
        mock_get_config,
        sample_gateway_request
    ):
        """Gateway should publish inference message to SNS topic."""
        mock_publisher = MagicMock()
        mock_get_publisher.return_value = mock_publisher

        mock_redis = MagicMock()
        mock_get_state_repo.return_value = mock_redis

        mock_config = MagicMock()
        mock_config.get.return_value = "inference"
        mock_get_config.return_value = mock_config

        from src.services.gateway.request_submission_service import RequestSubmissionService
        from src.objects.requests.gateway_request import GatewayRequest

        manager = RequestSubmissionService()
        request = GatewayRequest(**sample_gateway_request)

        manager.submit_request(request)

        mock_publisher.publish.assert_called_once()
        topic_name = mock_publisher.publish.call_args[0][0]
        assert topic_name == "inference"

    @patch('src.services.gateway.request_submission_service.get_config_service')
    @patch('src.services.gateway.request_submission_service.get_message_publisher')
    @patch('src.services.gateway.request_submission_service.get_state_repository')
    def test_inference_message_contains_required_fields(
        self,
        mock_get_state_repo,
        mock_get_publisher,
        mock_get_config,
        sample_gateway_request
    ):
        """Published inference message should contain all required fields."""
        mock_publisher = MagicMock()
        mock_get_publisher.return_value = mock_publisher

        mock_redis = MagicMock()
        mock_get_state_repo.return_value = mock_redis

        mock_config = MagicMock()
        mock_config.get.return_value = "inference"
        mock_get_config.return_value = mock_config

        from src.services.gateway.request_submission_service import RequestSubmissionService
        from src.objects.requests.gateway_request import GatewayRequest

        manager = RequestSubmissionService()
        request = GatewayRequest(**sample_gateway_request)

        manager.submit_request(request)

        published_message = json.loads(mock_publisher.publish.call_args[0][1])

        assert "request_id" in published_message
        assert "topic_name" in published_message
        assert "gateway_request" in published_message
        assert published_message["topic_name"] == "inference"

    @patch('src.services.gateway.request_submission_service.get_config_service')
    @patch('src.services.gateway.request_submission_service.get_message_publisher')
    @patch('src.services.gateway.request_submission_service.get_state_repository')
    def test_returns_accepted_response(
        self,
        mock_get_state_repo,
        mock_get_publisher,
        mock_get_config,
        sample_gateway_request
    ):
        """Gateway should return accepted response with request ID."""
        mock_publisher = MagicMock()
        mock_get_publisher.return_value = mock_publisher

        mock_redis = MagicMock()
        mock_get_state_repo.return_value = mock_redis

        mock_config = MagicMock()
        mock_config.get.return_value = "inference"
        mock_get_config.return_value = mock_config

        from src.services.gateway.request_submission_service import RequestSubmissionService
        from src.objects.requests.gateway_request import GatewayRequest
        from src.objects.enums.request_status import RequestStatus

        manager = RequestSubmissionService()
        request = GatewayRequest(**sample_gateway_request)

        response = manager.submit_request(request)

        assert response.request_id is not None
        assert response.status == RequestStatus.Accepted
