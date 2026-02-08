"""Unit tests for utils/services module."""
import pytest
from unittest.mock import MagicMock, patch


class TestSNSService:
    @patch('src.utils.services.aws.sns_service.boto3')
    @patch('src.utils.services.aws.sns_service.get_config_service')
    @patch('src.utils.services.aws.sns_service.Logger')
    def test_publish_success(self, mock_logger, mock_get_config, mock_boto3):
        mock_appconfig = MagicMock()
        mock_appconfig.get.return_value = "us-east-1"
        mock_get_config.return_value = mock_appconfig
        mock_sns_client = MagicMock()
        mock_sns_client.publish.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": 200},
            "MessageId": "msg-123"
        }
        mock_boto3.client.return_value = mock_sns_client

        from src.utils.services.aws.sns_service import SNSService

        service = SNSService()
        result = service.publish("arn:aws:sns:us-east-1:123:test", '{"test": "message"}')

        assert result is True
        mock_sns_client.publish.assert_called_once()

    @patch('src.utils.services.aws.sns_service.boto3')
    @patch('src.utils.services.aws.sns_service.get_config_service')
    @patch('src.utils.services.aws.sns_service.Logger')
    def test_publish_failure_raises(self, mock_logger, mock_get_config, mock_boto3):
        mock_appconfig = MagicMock()
        mock_appconfig.get.return_value = "us-east-1"
        mock_get_config.return_value = mock_appconfig
        mock_sns_client = MagicMock()
        mock_sns_client.publish.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": 500}
        }
        mock_boto3.client.return_value = mock_sns_client

        from src.utils.services.aws.sns_service import SNSService

        service = SNSService()

        with pytest.raises(Exception) as exc_info:
            service.publish("arn:aws:sns:us-east-1:123:test", '{"test": "message"}')

        assert "500" in str(exc_info.value)

    @patch('src.utils.services.aws.sns_service.boto3')
    @patch('src.utils.services.aws.sns_service.get_config_service')
    @patch('src.utils.services.aws.sns_service.Logger')
    def test_publish_resolves_topic_name_to_arn(self, mock_logger, mock_get_config, mock_boto3):
        """publish() should resolve logical topic name to SNS ARN internally."""
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "aws.region": "us-east-1",
            "sns.inference_topic_arn": "arn:aws:sns:us-east-1:123:inference",
            "sns.judge_topic_arn": "arn:aws:sns:us-east-1:123:judge"
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        mock_sns_client = MagicMock()
        mock_sns_client.publish.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": 200},
            "MessageId": "msg-123"
        }
        mock_boto3.client.return_value = mock_sns_client

        from src.utils.services.aws.sns_service import SNSService, get_sns_service
        get_sns_service.cache_clear()

        service = SNSService()
        service.publish("inference", '{"test": "message"}')

        call_args = mock_sns_client.publish.call_args[1]
        assert call_args["TopicArn"] == "arn:aws:sns:us-east-1:123:inference"


class TestSQSService:
    @patch('src.utils.services.aws.sqs_service.boto3')
    @patch('src.utils.services.aws.sqs_service.get_config_service')
    @patch('src.utils.services.aws.sqs_service.Logger')
    def test_receive_message_with_messages(self, mock_logger, mock_get_config, mock_boto3):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "aws.region": "us-east-1",
            "sqs.visibility_timeout_seconds": 300,
            "sqs.wait_time_seconds": 1
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        mock_sqs_client = MagicMock()
        mock_sqs_client.receive_message.return_value = {
            "Messages": [{"MessageId": "msg-1", "Body": "test"}]
        }
        mock_boto3.client.return_value = mock_sqs_client

        from src.utils.services.aws.sqs_service import SQSService, get_sqs_service
        get_sqs_service.cache_clear()

        service = SQSService()
        messages = service.receive_message("https://sqs.test.com/queue")

        assert len(messages) == 1
        assert messages[0]["MessageId"] == "msg-1"

    @patch('src.utils.services.aws.sqs_service.boto3')
    @patch('src.utils.services.aws.sqs_service.get_config_service')
    @patch('src.utils.services.aws.sqs_service.Logger')
    def test_receive_message_empty(self, mock_logger, mock_get_config, mock_boto3):
        mock_appconfig = MagicMock()
        mock_appconfig.get.return_value = 1
        mock_get_config.return_value = mock_appconfig
        mock_sqs_client = MagicMock()
        mock_sqs_client.receive_message.return_value = {}
        mock_boto3.client.return_value = mock_sqs_client

        from src.utils.services.aws.sqs_service import SQSService, get_sqs_service
        get_sqs_service.cache_clear()

        service = SQSService()
        messages = service.receive_message("https://sqs.test.com/queue")

        assert messages == []

    @patch('src.utils.services.aws.sqs_service.boto3')
    @patch('src.utils.services.aws.sqs_service.get_config_service')
    @patch('src.utils.services.aws.sqs_service.Logger')
    def test_delete_message(self, mock_logger, mock_get_config, mock_boto3):
        mock_appconfig = MagicMock()
        mock_appconfig.get.return_value = "us-east-1"
        mock_get_config.return_value = mock_appconfig
        mock_sqs_client = MagicMock()
        mock_sqs_client.delete_message.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
        mock_boto3.client.return_value = mock_sqs_client

        from src.utils.services.aws.sqs_service import SQSService, get_sqs_service
        get_sqs_service.cache_clear()

        service = SQSService()
        result = service.delete_message("https://sqs.test.com/queue", "receipt-handle-123")

        mock_sqs_client.delete_message.assert_called_once_with(
            QueueUrl="https://sqs.test.com/queue",
            ReceiptHandle="receipt-handle-123"
        )

    @patch('src.utils.services.aws.sqs_service.boto3')
    @patch('src.utils.services.aws.sqs_service.get_config_service')
    @patch('src.utils.services.aws.sqs_service.Logger')
    def test_change_message_visibility(self, mock_logger, mock_get_config, mock_boto3):
        mock_appconfig = MagicMock()
        mock_appconfig.get.return_value = "us-east-1"
        mock_get_config.return_value = mock_appconfig
        mock_sqs_client = MagicMock()
        mock_boto3.client.return_value = mock_sqs_client

        from src.utils.services.aws.sqs_service import SQSService, get_sqs_service
        get_sqs_service.cache_clear()

        service = SQSService()
        service.change_message_visibility("https://sqs.test.com/queue", "receipt-handle", 600)

        mock_sqs_client.change_message_visibility.assert_called_once_with(
            QueueUrl="https://sqs.test.com/queue",
            ReceiptHandle="receipt-handle",
            VisibilityTimeout=600
        )


class TestRedisClient:
    @patch('src.utils.services.clients.redis_client.httpx.Client')
    @patch('src.utils.services.clients.redis_client.get_config_service')
    def test_create_request(self, mock_get_config, mock_httpx_client):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "services.redis.host": "localhost",
            "services.redis.port": 8001
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "request_id": "test-123",
            "gateway_request": {"prompt": "test", "target_model": {"name": "ChatGPT"}, "api_key": "sk-key", "judge_model": {"name": "qwen2.5", "version": "latest"}},
            "stage": "Gateway",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.return_value.post.return_value = mock_response

        from src.utils.services.clients.redis_client import RedisClient, get_state_repository
        get_state_repository.cache_clear()

        from src.objects.enums.processed_request import ProcessedRequest
        from src.objects.requests.gateway_request import GatewayRequest
        from src.objects.enums.request_stage import RequestStage

        client = RedisClient()
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

        result = client.create_request(request)
        assert result.request_id == "test-123"

    @patch('src.utils.services.clients.redis_client.httpx.Client')
    @patch('src.utils.services.clients.redis_client.get_config_service')
    def test_get_request_found(self, mock_get_config, mock_httpx_client):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "services.redis.host": "localhost",
            "services.redis.port": 8001
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "request_id": "test-123",
            "gateway_request": {"prompt": "test", "target_model": {"name": "ChatGPT"}, "api_key": "sk-key", "judge_model": {"name": "qwen2.5", "version": "latest"}},
            "stage": "Gateway",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.return_value.get.return_value = mock_response

        from src.utils.services.clients.redis_client import RedisClient, get_state_repository
        get_state_repository.cache_clear()

        client = RedisClient()
        result = client.get_request("test-123")

        assert result is not None
        assert result.request_id == "test-123"

    @patch('src.utils.services.clients.redis_client.httpx.Client')
    @patch('src.utils.services.clients.redis_client.get_config_service')
    def test_get_request_not_found(self, mock_get_config, mock_httpx_client):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "services.redis.host": "localhost",
            "services.redis.port": 8001
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_httpx_client.return_value.get.return_value = mock_response

        from src.utils.services.clients.redis_client import RedisClient, get_state_repository
        get_state_repository.cache_clear()

        client = RedisClient()
        result = client.get_request("non-existent")

        assert result is None

    @patch('src.utils.services.clients.redis_client.httpx.Client')
    @patch('src.utils.services.clients.redis_client.get_config_service')
    def test_delete_request(self, mock_get_config, mock_httpx_client):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "services.redis.host": "localhost",
            "services.redis.port": 8001
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.return_value.delete.return_value = mock_response

        from src.utils.services.clients.redis_client import RedisClient, get_state_repository
        get_state_repository.cache_clear()

        client = RedisClient()
        result = client.delete_request("test-123")

        assert result is True

    @patch('src.utils.services.clients.redis_client.httpx.Client')
    @patch('src.utils.services.clients.redis_client.get_config_service')
    def test_health_check_healthy(self, mock_get_config, mock_httpx_client):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "services.redis.host": "localhost",
            "services.redis.port": 8001
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_httpx_client.return_value.get.return_value = mock_response

        from src.utils.services.clients.redis_client import RedisClient, get_state_repository
        get_state_repository.cache_clear()

        client = RedisClient()
        assert client.health_check() is True


class TestPersistenceClient:
    @patch('src.utils.services.clients.persistence_client.httpx.Client')
    @patch('src.utils.services.clients.persistence_client.get_config_service')
    def test_create_history(self, mock_get_config, mock_httpx_client):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "services.persistence.host": "localhost",
            "services.persistence.port": 8002
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 1,
            "request_id": "test-123",
            "prompt": "test",
            "target_model": "ChatGPT",
            "judge_model": "qwen2.5",
            "status": "Completed",
            "created_at": "2024-01-01T00:00:00",
            "completed_at": "2024-01-01T00:00:00"
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.return_value.post.return_value = mock_response

        from src.utils.services.clients.persistence_client import PersistenceClient, get_persistence_gateway
        get_persistence_gateway.cache_clear()

        client = PersistenceClient()
        result = client.create_history({"request_id": "test-123", "status": "Completed"})

        assert result["request_id"] == "test-123"
        assert result["id"] == 1

    @patch('src.utils.services.clients.persistence_client.httpx.Client')
    @patch('src.utils.services.clients.persistence_client.get_config_service')
    def test_get_history(self, mock_get_config, mock_httpx_client):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "services.persistence.host": "localhost",
            "services.persistence.port": 8002
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "id": 1,
                "request_id": "test-123",
                "prompt": "test",
                "target_model": "ChatGPT",
                "judge_model": "qwen2.5",
                "status": "Completed",
                "created_at": "2024-01-01T00:00:00",
                "completed_at": "2024-01-01T00:00:00"
            }
        ]
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.return_value.get.return_value = mock_response

        from src.utils.services.clients.persistence_client import PersistenceClient, get_persistence_gateway
        get_persistence_gateway.cache_clear()

        client = PersistenceClient()
        results = client.get_history(limit=10, offset=0)

        assert len(results) == 1
        assert results[0]["request_id"] == "test-123"

    @patch('src.utils.services.clients.persistence_client.httpx.Client')
    @patch('src.utils.services.clients.persistence_client.get_config_service')
    def test_get_history_by_request_id_not_found(self, mock_get_config, mock_httpx_client):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "services.persistence.host": "localhost",
            "services.persistence.port": 8002
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_httpx_client.return_value.get.return_value = mock_response

        from src.utils.services.clients.persistence_client import PersistenceClient, get_persistence_gateway
        get_persistence_gateway.cache_clear()

        client = PersistenceClient()
        result = client.get_history_by_request_id("non-existent")

        assert result is None


class TestOpenAIClient:
    @patch('src.utils.services.llm.openai_client.OpenAI')
    def test_chat_completion(self, mock_openai_class):
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_choice = MagicMock()
        mock_choice.message.content = "The answer is 4."
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 5
        mock_usage.total_tokens = 15

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.model = "gpt-4o-mini"
        mock_response.usage = mock_usage
        mock_client.chat.completions.create.return_value = mock_response

        from src.utils.services.llm.openai_client import OpenAIClient

        client = OpenAIClient(api_key="sk-test-key")
        result = client._chat_completion(prompt="What is 2+2?")

        assert result.response == "The answer is 4."
        assert result.model == "gpt-4o-mini"
        assert result.prompt_tokens == 10
        assert result.completion_tokens == 5
        assert result.total_tokens == 15

    @patch('src.utils.services.llm.openai_client.OpenAI')
    def test_chat_completion_with_system_prompt(self, mock_openai_class):
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_choice = MagicMock()
        mock_choice.message.content = "Test response"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.model = "gpt-4"
        mock_response.usage = None
        mock_client.chat.completions.create.return_value = mock_response

        from src.utils.services.llm.openai_client import OpenAIClient
        from src.interfaces.llm_provider import InferenceConfig

        client = OpenAIClient(api_key="sk-test")
        config = InferenceConfig(
            model="gpt-4",
            temperature=0.7,
            system_prompt="You are a helpful assistant"
        )
        result = client._chat_completion(prompt="Hello", config=config)

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"


class TestJudgeInferenceClient:
    @patch('src.utils.services.clients.judge_inference_client.httpx.Client')
    @patch('src.utils.services.clients.judge_inference_client.get_config_service')
    def test_judge_returns_dict(self, mock_get_config, mock_httpx_client):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "services.judge_inference.host": "localhost",
            "services.judge_inference.port": 8003
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        from src.utils.services.clients.judge_inference_client import JudgeInferenceClient, get_judge_gateway
        get_judge_gateway.cache_clear()

        client = JudgeInferenceClient()
        result = client.judge(
            original_prompt="What is 2+2?",
            model_response="The answer is 4.",
            model="qwen2.5:latest"
        )

        assert result["score"] == 0.5
        assert "Placeholder" in result["reasoning"]
        assert result["model"] == "qwen2.5:latest"
        assert result["categories"] is not None

    @patch('src.utils.services.clients.judge_inference_client.httpx.Client')
    @patch('src.utils.services.clients.judge_inference_client.get_config_service')
    def test_is_healthy_returns_false_on_error(self, mock_get_config, mock_httpx_client):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "services.judge_inference.host": "localhost",
            "services.judge_inference.port": 8003
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        mock_httpx_client.return_value.get.side_effect = Exception("Connection refused")

        from src.utils.services.clients.judge_inference_client import JudgeInferenceClient, get_judge_gateway
        get_judge_gateway.cache_clear()

        client = JudgeInferenceClient()
        assert client.is_healthy() is False
