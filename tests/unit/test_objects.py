"""Unit tests for objects module."""
import pytest
from datetime import datetime
from pydantic import ValidationError, SecretStr

from src.objects.enums.request_stage import RequestStage
from src.objects.enums.request_status import RequestStatus
from src.objects.enums.processed_request import ProcessedRequest
from src.objects.requests.gateway_request import GatewayRequest
from src.objects.responses.gateway_response import GatewayResponse
from src.objects.results.inference_result import InferenceResult
from src.objects.results.judge_result import JudgeResult
from src.objects.messages.base_message import BaseMessage
from src.objects.messages.inference_message import InferenceMessage
from src.objects.messages.judge_message import JudgeMessage
from src.objects.target_models.target_model import TargetModel
from src.objects.judge_models.judge_model import JudgeModel


class TestRequestStage:
    def test_all_stages_exist(self):
        assert RequestStage.Gateway == "Gateway"
        assert RequestStage.Inference == "Inference"
        assert RequestStage.Judge == "Judge"
        assert RequestStage.Completed == "Completed"
        assert RequestStage.Failed == "Failed"

    def test_stage_is_string_enum(self):
        assert isinstance(RequestStage.Gateway, str)
        assert RequestStage.Gateway.value == "Gateway"


class TestRequestStatus:
    def test_all_statuses_exist(self):
        assert RequestStatus.Accepted == "Accepted"
        assert RequestStatus.Rejected == "Rejected"


class TestTargetModel:
    def test_create_target_model(self):
        model = TargetModel(name="ChatGPT")
        assert model.name == "ChatGPT"

    def test_target_model_serialization(self):
        model = TargetModel(name="GPT-4")
        data = model.model_dump()
        assert data == {"name": "GPT-4"}

    def test_target_model_requires_name(self):
        with pytest.raises(ValidationError):
            TargetModel()


class TestJudgeModel:
    def test_create_judge_model(self):
        model = JudgeModel(name="qwen2.5", version="latest")
        assert model.name == "qwen2.5"
        assert model.version == "latest"

    def test_judge_model_serialization(self):
        model = JudgeModel(name="qwen2.5", version="1.0")
        data = model.model_dump()
        assert data == {"name": "qwen2.5", "version": "1.0"}


class TestGatewayRequest:
    def test_create_gateway_request(self, sample_gateway_request):
        request = GatewayRequest(**sample_gateway_request)
        assert request.prompt == "What is 2+2?"
        assert request.target_model.name == "ChatGPT"
        assert request.judge_model.name == "qwen2.5"

    def test_api_key_is_secret(self, sample_gateway_request):
        request = GatewayRequest(**sample_gateway_request)
        assert isinstance(request.api_key, SecretStr)
        assert request.api_key.get_secret_value() == "sk-test-key"

    def test_gateway_request_validation(self):
        with pytest.raises(ValidationError):
            GatewayRequest(prompt="test")  # Missing required fields


class TestGatewayResponse:
    def test_create_gateway_response(self):
        response = GatewayResponse(
            request_id="test-123",
            status=RequestStatus.Accepted
        )
        assert response.request_id == "test-123"
        assert response.status == RequestStatus.Accepted


class TestInferenceResult:
    def test_create_inference_result(self, sample_inference_result):
        result = InferenceResult(**sample_inference_result)
        assert result.response == "2+2 equals 4."
        assert result.model == "gpt-4o-mini"
        assert result.latency_ms == 150.5
        assert result.total_tokens == 18

    def test_inference_result_optional_fields(self):
        result = InferenceResult(
            response="test",
            model="gpt-4",
            latency_ms=100.0
        )
        assert result.prompt_tokens is None
        assert result.completion_tokens is None
        assert result.total_tokens is None


class TestJudgeResult:
    def test_create_judge_result(self, sample_judge_result):
        result = JudgeResult(**sample_judge_result)
        assert result.score == 0.95
        assert result.reasoning == "The answer is correct and concise."
        assert result.categories["accuracy"] == 1.0
        assert result.model == "qwen2.5:latest"

    def test_judge_result_optional_categories(self):
        result = JudgeResult(
            score=0.5,
            reasoning="test",
            model="test-model",
            latency_ms=100.0
        )
        assert result.categories is None


class TestProcessedRequest:
    def test_create_processed_request(self, sample_gateway_request):
        request = ProcessedRequest(
            request_id="test-123",
            gateway_request=GatewayRequest(**sample_gateway_request),
            stage=RequestStage.Gateway
        )
        assert request.request_id == "test-123"
        assert request.stage == RequestStage.Gateway
        assert request.inference_result is None
        assert request.judge_result is None

    def test_processed_request_with_results(self, sample_gateway_request, sample_inference_result, sample_judge_result):
        request = ProcessedRequest(
            request_id="test-123",
            gateway_request=GatewayRequest(**sample_gateway_request),
            stage=RequestStage.Completed,
            inference_result=InferenceResult(**sample_inference_result),
            judge_result=JudgeResult(**sample_judge_result)
        )
        assert request.stage == RequestStage.Completed
        assert request.inference_result.response == "2+2 equals 4."
        assert request.judge_result.score == 0.95

    def test_processed_request_timestamps(self, sample_gateway_request):
        request = ProcessedRequest(
            request_id="test-123",
            gateway_request=GatewayRequest(**sample_gateway_request),
            stage=RequestStage.Gateway
        )
        assert isinstance(request.created_at, datetime)
        assert isinstance(request.updated_at, datetime)


class TestInferenceMessage:
    def test_create_inference_message(self, sample_gateway_request):
        message = InferenceMessage(
            request_id="test-123",
            gateway_request=GatewayRequest(**sample_gateway_request)
        )
        assert message.request_id == "test-123"
        assert message.topic_name == "inference"
        assert message.gateway_request.prompt == "What is 2+2?"

    def test_inference_message_serialization(self, sample_gateway_request):
        message = InferenceMessage(
            request_id="test-123",
            gateway_request=GatewayRequest(**sample_gateway_request)
        )
        data = message.model_dump()
        assert data["request_id"] == "test-123"
        assert data["topic_name"] == "inference"


class TestJudgeMessage:
    def test_create_judge_message(self, sample_gateway_request, sample_inference_result):
        message = JudgeMessage(
            request_id="test-123",
            gateway_request=GatewayRequest(**sample_gateway_request),
            inference_result=InferenceResult(**sample_inference_result)
        )
        assert message.request_id == "test-123"
        assert message.topic_name == "judge"
        assert message.inference_result.response == "2+2 equals 4."
