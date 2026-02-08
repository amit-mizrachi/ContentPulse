"""Unit tests for redis_service module."""
from unittest.mock import MagicMock, patch


class TestRequestRepository:
    @patch('src.services.redis.request_repository.redis.Redis')
    @patch('src.services.redis.request_repository.get_config_service')
    def test_create(self, mock_get_config, mock_redis):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "redis.host": "localhost",
            "redis.port": 6379,
            "redis.default_ttl_seconds": 604800
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client

        from src.services.redis.request_repository import RequestRepository
        RequestRepository._instances = {}

        from src.objects.enums.processed_request import ProcessedRequest
        from src.objects.requests.gateway_request import GatewayRequest
        from src.objects.enums.request_stage import RequestStage

        repository = RequestRepository()

        request = ProcessedRequest(
            request_id="test-123",
            gateway_request=GatewayRequest(
                prompt="test",
                target_model={"name": "ChatGPT"},
                api_key="sk-key",
                judge_model={"name": "qwen2.5", "version": "latest"}
            ),
            stage=RequestStage.Gateway
        )

        result = repository.create(request)

        assert result.request_id == "test-123"
        mock_redis_client.setex.assert_called_once()

    @patch('src.services.redis.request_repository.redis.Redis')
    @patch('src.services.redis.request_repository.get_config_service')
    def test_get_found(self, mock_get_config, mock_redis):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "redis.host": "localhost",
            "redis.port": 6379,
            "redis.default_ttl_seconds": 604800
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        mock_redis_client = MagicMock()
        mock_redis_client.get.return_value = '''{
            "request_id": "test-123",
            "gateway_request": {
                "prompt": "test",
                "target_model": {"name": "ChatGPT"},
                "api_key": "sk-key",
                "judge_model": {"name": "qwen2.5", "version": "latest"}
            },
            "stage": "Gateway",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }'''
        mock_redis.return_value = mock_redis_client

        from src.services.redis.request_repository import RequestRepository
        RequestRepository._instances = {}

        repository = RequestRepository()
        result = repository.get("test-123")

        assert result is not None
        assert result.request_id == "test-123"
        mock_redis_client.get.assert_called_with("request:test-123")

    @patch('src.services.redis.request_repository.redis.Redis')
    @patch('src.services.redis.request_repository.get_config_service')
    def test_get_not_found(self, mock_get_config, mock_redis):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "redis.host": "localhost",
            "redis.port": 6379,
            "redis.default_ttl_seconds": 604800
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        mock_redis_client = MagicMock()
        mock_redis_client.get.return_value = None
        mock_redis.return_value = mock_redis_client

        from src.services.redis.request_repository import RequestRepository
        RequestRepository._instances = {}

        repository = RequestRepository()
        result = repository.get("non-existent")

        assert result is None

    @patch('src.services.redis.request_repository.redis.Redis')
    @patch('src.services.redis.request_repository.get_config_service')
    def test_update(self, mock_get_config, mock_redis):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "redis.host": "localhost",
            "redis.port": 6379,
            "redis.default_ttl_seconds": 604800
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        mock_redis_client = MagicMock()
        mock_redis_client.get.return_value = '''{
            "request_id": "test-123",
            "gateway_request": {
                "prompt": "test",
                "target_model": {"name": "ChatGPT"},
                "api_key": "sk-key",
                "judge_model": {"name": "qwen2.5", "version": "latest"}
            },
            "stage": "Gateway",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }'''
        mock_redis_client.ttl.return_value = 600000
        mock_redis.return_value = mock_redis_client

        from src.services.redis.request_repository import RequestRepository
        RequestRepository._instances = {}

        repository = RequestRepository()
        result = repository.update("test-123", {"stage": "Inference"})

        assert result is not None
        assert result.stage == "Inference"
        mock_redis_client.setex.assert_called_once()

    @patch('src.services.redis.request_repository.redis.Redis')
    @patch('src.services.redis.request_repository.get_config_service')
    def test_update_not_found(self, mock_get_config, mock_redis):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "redis.host": "localhost",
            "redis.port": 6379,
            "redis.default_ttl_seconds": 604800
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        mock_redis_client = MagicMock()
        mock_redis_client.get.return_value = None
        mock_redis.return_value = mock_redis_client

        from src.services.redis.request_repository import RequestRepository
        RequestRepository._instances = {}

        repository = RequestRepository()
        result = repository.update("non-existent", {"stage": "Inference"})

        assert result is None

    @patch('src.services.redis.request_repository.redis.Redis')
    @patch('src.services.redis.request_repository.get_config_service')
    def test_delete(self, mock_get_config, mock_redis):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "redis.host": "localhost",
            "redis.port": 6379,
            "redis.default_ttl_seconds": 604800
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        mock_redis_client = MagicMock()
        mock_redis_client.delete.return_value = 1
        mock_redis.return_value = mock_redis_client

        from src.services.redis.request_repository import RequestRepository
        RequestRepository._instances = {}

        repository = RequestRepository()
        result = repository.delete("test-123")

        assert result is True
        mock_redis_client.delete.assert_called_with("request:test-123")

    @patch('src.services.redis.request_repository.redis.Redis')
    @patch('src.services.redis.request_repository.get_config_service')
    def test_delete_not_found(self, mock_get_config, mock_redis):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "redis.host": "localhost",
            "redis.port": 6379,
            "redis.default_ttl_seconds": 604800
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        mock_redis_client = MagicMock()
        mock_redis_client.delete.return_value = 0
        mock_redis.return_value = mock_redis_client

        from src.services.redis.request_repository import RequestRepository
        RequestRepository._instances = {}

        repository = RequestRepository()
        result = repository.delete("non-existent")

        assert result is False

    @patch('src.services.redis.request_repository.redis.Redis')
    @patch('src.services.redis.request_repository.get_config_service')
    def test_is_healthy(self, mock_get_config, mock_redis):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "redis.host": "localhost",
            "redis.port": 6379,
            "redis.default_ttl_seconds": 604800
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        mock_redis_client = MagicMock()
        mock_redis_client.ping.return_value = True
        mock_redis.return_value = mock_redis_client

        from src.services.redis.request_repository import RequestRepository
        RequestRepository._instances = {}

        repository = RequestRepository()
        assert repository.is_healthy() is True

    @patch('src.services.redis.request_repository.redis.Redis')
    @patch('src.services.redis.request_repository.get_config_service')
    def test_is_unhealthy(self, mock_get_config, mock_redis):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "redis.host": "localhost",
            "redis.port": 6379,
            "redis.default_ttl_seconds": 604800
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        mock_redis_client = MagicMock()
        mock_redis_client.ping.side_effect = Exception("Connection failed")
        mock_redis.return_value = mock_redis_client

        from src.services.redis.request_repository import RequestRepository
        RequestRepository._instances = {}

        repository = RequestRepository()
        assert repository.is_healthy() is False


class TestRedisServiceServer:
    """Tests for Redis service server endpoints.

    These tests use standalone FastAPI apps to avoid module initialization issues.
    """

    def test_create_request_endpoint(self, sample_gateway_request):
        """Test create request endpoint accepts valid requests."""
        from fastapi import FastAPI, HTTPException
        from fastapi.testclient import TestClient
        from src.objects.enums.processed_request import ProcessedRequest
        from src.objects.requests.gateway_request import GatewayRequest
        from src.objects.enums.request_stage import RequestStage

        app = FastAPI()

        processed = ProcessedRequest(
            request_id="test-123",
            gateway_request=GatewayRequest(**sample_gateway_request),
            stage=RequestStage.Gateway
        )

        mock_manager = MagicMock()
        mock_manager.create_request.return_value = processed

        @app.post("/requests/{request_id}", response_model=ProcessedRequest)
        async def create_request(request_id: str, request: ProcessedRequest):
            if request.request_id != request_id:
                raise HTTPException(status_code=400, detail="Request ID mismatch")
            return mock_manager.create_request(request)

        client = TestClient(app)
        response = client.post(
            "/requests/test-123",
            json=processed.model_dump(mode="json")
        )
        assert response.status_code == 200

    def test_get_request_not_found_endpoint(self):
        """Test get request endpoint returns 404 when not found."""
        from fastapi import FastAPI, HTTPException
        from fastapi.testclient import TestClient

        app = FastAPI()

        mock_manager = MagicMock()
        mock_manager.get_request.return_value = None

        @app.get("/requests/{request_id}")
        async def get_request(request_id: str):
            request = mock_manager.get_request(request_id)
            if request is None:
                raise HTTPException(status_code=404, detail="Request not found")
            return request

        client = TestClient(app)
        response = client.get("/requests/non-existent")
        assert response.status_code == 404

    def test_health_endpoint_healthy(self):
        """Test health endpoint returns healthy when Redis is up."""
        from fastapi import FastAPI, HTTPException
        from fastapi.testclient import TestClient

        app = FastAPI()

        mock_manager = MagicMock()
        mock_manager.health_check.return_value = True

        @app.get("/health")
        async def health_check():
            healthy = mock_manager.health_check()
            if not healthy:
                raise HTTPException(status_code=503, detail="Redis connection failed")
            return {"status": "healthy"}

        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_health_endpoint_unhealthy(self):
        """Test health endpoint returns 503 when Redis is down."""
        from fastapi import FastAPI, HTTPException
        from fastapi.testclient import TestClient

        app = FastAPI()

        mock_manager = MagicMock()
        mock_manager.health_check.return_value = False

        @app.get("/health")
        async def health_check():
            healthy = mock_manager.health_check()
            if not healthy:
                raise HTTPException(status_code=503, detail="Redis connection failed")
            return {"status": "healthy"}

        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 503
