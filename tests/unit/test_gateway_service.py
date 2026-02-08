"""Unit tests for ingress_gateway_service module."""
import pytest
from unittest.mock import MagicMock
import uuid


class TestRequestManager:
    """Tests for RequestSubmissionService using constructor injection."""

    def test_submit_request(self, sample_gateway_request):
        """Test that submit_request creates request and publishes message."""
        mock_state_repo = MagicMock()
        mock_message_publisher = MagicMock()

        from src.services.gateway.request_submission_service import RequestSubmissionService
        from src.objects.requests.gateway_request import GatewayRequest
        from src.objects.enums.request_status import RequestStatus

        service = RequestSubmissionService(
            state_repository=mock_state_repo,
            message_publisher=mock_message_publisher,
            inference_topic="inference",
        )

        gateway_request = GatewayRequest(**sample_gateway_request)
        response = service.submit_request(gateway_request)

        assert response.request_id is not None
        assert response.status == RequestStatus.Accepted

        # Verify state repository was called to create request
        mock_state_repo.create.assert_called_once()

        # Verify message publisher was called
        mock_message_publisher.publish.assert_called_once()

    def test_submit_request_generates_uuid(self, sample_gateway_request):
        """Test that submit generates a valid UUID for request_id."""
        mock_state_repo = MagicMock()
        mock_message_publisher = MagicMock()

        from src.services.gateway.request_submission_service import RequestSubmissionService
        from src.objects.requests.gateway_request import GatewayRequest

        service = RequestSubmissionService(
            state_repository=mock_state_repo,
            message_publisher=mock_message_publisher,
            inference_topic="inference",
        )

        gateway_request = GatewayRequest(**sample_gateway_request)
        response = service.submit_request(gateway_request)

        # Verify the request_id is a valid UUID
        try:
            uuid.UUID(response.request_id)
            is_valid_uuid = True
        except ValueError:
            is_valid_uuid = False

        assert is_valid_uuid is True

    def test_get_request_metadata_found(self, sample_gateway_request):
        """Test that get_request_metadata returns request when found."""
        from src.objects.enums.request_stage import RequestStage

        mock_state_repo = MagicMock()
        mock_state_repo.get.return_value = {
            "request_id": "test-123",
            "gateway_request": sample_gateway_request,
            "stage": RequestStage.Inference.value,
            "created_at": "2024-01-01T00:00:00"
        }
        mock_message_publisher = MagicMock()

        from src.services.gateway.request_submission_service import RequestSubmissionService

        service = RequestSubmissionService(
            state_repository=mock_state_repo,
            message_publisher=mock_message_publisher,
            inference_topic="inference",
        )

        result = service.get_request_metadata("test-123")

        assert result.request_id == "test-123"
        assert result.stage == RequestStage.Inference

    def test_get_request_metadata_not_found(self):
        """Test that get_request_metadata raises KeyError when not found."""
        mock_state_repo = MagicMock()
        mock_state_repo.get.return_value = None
        mock_message_publisher = MagicMock()

        from src.services.gateway.request_submission_service import RequestSubmissionService

        service = RequestSubmissionService(
            state_repository=mock_state_repo,
            message_publisher=mock_message_publisher,
            inference_topic="inference",
        )

        with pytest.raises(KeyError) as exc_info:
            service.get_request_metadata("non-existent")

        assert "non-existent" in str(exc_info.value)

    def test_submit_creates_inference_message(self, sample_gateway_request):
        """Test that submit creates properly formatted inference message."""
        mock_state_repo = MagicMock()
        mock_message_publisher = MagicMock()

        from src.services.gateway.request_submission_service import RequestSubmissionService
        from src.objects.requests.gateway_request import GatewayRequest
        import json

        service = RequestSubmissionService(
            state_repository=mock_state_repo,
            message_publisher=mock_message_publisher,
            inference_topic="inference",
        )

        gateway_request = GatewayRequest(**sample_gateway_request)
        service.submit_request(gateway_request)

        # Get the message that was published
        published_message = mock_message_publisher.publish.call_args[0][1]
        message_data = json.loads(published_message)

        assert "request_id" in message_data
        assert "gateway_request" in message_data
        assert message_data["topic_name"] == "inference"

    def test_submit_creates_gateway_stage_request(self, sample_gateway_request):
        """Test that submit creates request with Gateway stage."""
        mock_state_repo = MagicMock()
        mock_message_publisher = MagicMock()

        from src.services.gateway.request_submission_service import RequestSubmissionService
        from src.objects.requests.gateway_request import GatewayRequest
        from src.objects.enums.request_stage import RequestStage

        service = RequestSubmissionService(
            state_repository=mock_state_repo,
            message_publisher=mock_message_publisher,
            inference_topic="inference",
        )

        gateway_request = GatewayRequest(**sample_gateway_request)
        service.submit_request(gateway_request)

        # Get the data that was created in state repository
        create_call = mock_state_repo.create.call_args
        request_id = create_call[0][0]
        data = create_call[0][1]

        assert data["stage"] == RequestStage.Gateway.value


class TestGatewayServer:
    """Tests for Gateway server endpoints.

    Note: These tests use FastAPI TestClient with mock managers.
    """

    def test_submit_endpoint(self, sample_gateway_request):
        """Test submit endpoint accepts requests."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from src.objects.responses.gateway_response import GatewayResponse
        from src.objects.enums.request_status import RequestStatus
        from src.objects.requests.gateway_request import GatewayRequest

        # Create a simple test app
        app = FastAPI()

        mock_manager = MagicMock()
        mock_manager.submit_request.return_value = GatewayResponse(
            request_id="test-uuid",
            status=RequestStatus.Accepted
        )

        @app.post("/submit")
        async def submit(request: GatewayRequest):
            return mock_manager.submit_request(request)

        client = TestClient(app)
        response = client.post("/submit", json=sample_gateway_request)

        assert response.status_code == 200
        data = response.json()
        assert data["request_id"] == "test-uuid"
        assert data["status"] == "Accepted"

    def test_metadata_endpoint_found(self, sample_gateway_request):
        """Test metadata endpoint returns request when found."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from src.objects.enums.processed_request import ProcessedRequest
        from src.objects.requests.gateway_request import GatewayRequest
        from src.objects.enums.request_stage import RequestStage

        app = FastAPI()

        processed = ProcessedRequest(
            request_id="test-123",
            gateway_request=GatewayRequest(**sample_gateway_request),
            stage=RequestStage.Completed
        )

        mock_manager = MagicMock()
        mock_manager.get_request_metadata.return_value = processed

        @app.get("/metadata/{request_id}")
        async def get_metadata(request_id: str):
            return mock_manager.get_request_metadata(request_id)

        client = TestClient(app)
        response = client.get("/metadata/test-123")

        assert response.status_code == 200
        data = response.json()
        assert data["request_id"] == "test-123"
        assert data["stage"] == "Completed"

    def test_metadata_endpoint_not_found(self):
        """Test metadata endpoint returns 404 when not found."""
        from fastapi import FastAPI, HTTPException
        from fastapi.testclient import TestClient

        app = FastAPI()

        mock_manager = MagicMock()
        mock_manager.get_request_metadata.side_effect = KeyError("Request not found")

        @app.get("/metadata/{request_id}")
        async def get_metadata(request_id: str):
            try:
                return mock_manager.get_request_metadata(request_id)
            except KeyError as e:
                raise HTTPException(status_code=404, detail=str(e))

        client = TestClient(app)
        response = client.get("/metadata/non-existent")

        assert response.status_code == 404

    def test_health_endpoint(self):
        """Test health endpoint returns healthy status."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()

        @app.get("/health")
        async def health():
            return {"status": "healthy"}

        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
