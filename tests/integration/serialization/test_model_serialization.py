"""Integration tests for model serialization.

Tests verify that Pydantic models correctly serialize and deserialize
throughout the request lifecycle, ensuring data integrity across service boundaries.
"""
import pytest


class TestGatewayRequestSerialization:
    """Tests for GatewayRequest model serialization."""

    def test_serializes_to_json(self, sample_gateway_request):
        """GatewayRequest should serialize to valid JSON."""
        from src.objects.requests.gateway_request import GatewayRequest

        request = GatewayRequest(**sample_gateway_request)
        json_str = request.model_dump_json()

        assert isinstance(json_str, str)
        assert "prompt" in json_str
        assert "target_model" in json_str

    def test_deserializes_from_json(self, sample_gateway_request):
        """GatewayRequest should deserialize from JSON correctly."""
        from src.objects.requests.gateway_request import GatewayRequest

        request = GatewayRequest(**sample_gateway_request)
        json_str = request.model_dump_json()
        recovered = GatewayRequest.model_validate_json(json_str)

        assert recovered.prompt == sample_gateway_request["prompt"]
        assert recovered.target_model.name == sample_gateway_request["target_model"]["name"]

    def test_api_key_is_exposed_in_json_serialization(self, sample_gateway_request):
        """API key should be exposed in JSON for inter-service communication."""
        from src.objects.requests.gateway_request import GatewayRequest
        from pydantic import SecretStr

        request = GatewayRequest(**sample_gateway_request)
        json_str = request.model_dump_json()

        # API key is exposed in JSON (needed for inter-service message passing)
        assert sample_gateway_request["api_key"] in json_str

    def test_api_key_preserved_in_dict_serialization(self, sample_gateway_request):
        """API key value can be accessed via model_dump and original object."""
        from src.objects.requests.gateway_request import GatewayRequest
        from pydantic import SecretStr

        request = GatewayRequest(**sample_gateway_request)

        # With mode="json", field_serializer exposes the value for inter-service use
        json_dict = request.model_dump(mode="json")
        assert json_dict["api_key"] == sample_gateway_request["api_key"]

        # Original object still has SecretStr type
        assert isinstance(request.api_key, SecretStr)
        assert request.api_key.get_secret_value() == sample_gateway_request["api_key"]


class TestProcessedRequestSerialization:
    """Tests for ProcessedRequest model serialization."""

    def test_serializes_gateway_stage(self, sample_gateway_request):
        """ProcessedRequest at Gateway stage should serialize correctly."""
        from src.objects.enums.processed_request import ProcessedRequest
        from src.objects.requests.gateway_request import GatewayRequest
        from src.objects.enums.request_stage import RequestStage

        processed = ProcessedRequest(
            request_id="test-123",
            gateway_request=GatewayRequest(**sample_gateway_request),
            stage=RequestStage.Gateway
        )

        json_str = processed.model_dump_json()
        recovered = ProcessedRequest.model_validate_json(json_str)

        assert recovered.request_id == "test-123"
        assert recovered.stage == RequestStage.Gateway
        assert recovered.inference_result is None
        assert recovered.judge_result is None

    def test_serializes_completed_stage_with_results(
        self,
        sample_gateway_request,
        sample_inference_result,
        sample_judge_result
    ):
        """ProcessedRequest at Completed stage should serialize with all results."""
        from src.objects.enums.processed_request import ProcessedRequest
        from src.objects.requests.gateway_request import GatewayRequest
        from src.objects.enums.request_stage import RequestStage
        from src.objects.results.inference_result import InferenceResult
        from src.objects.results.judge_result import JudgeResult

        processed = ProcessedRequest(
            request_id="test-123",
            gateway_request=GatewayRequest(**sample_gateway_request),
            stage=RequestStage.Completed,
            inference_result=InferenceResult(**sample_inference_result),
            judge_result=JudgeResult(**sample_judge_result)
        )

        json_str = processed.model_dump_json()
        recovered = ProcessedRequest.model_validate_json(json_str)

        assert recovered.stage == RequestStage.Completed
        assert recovered.inference_result.response == sample_inference_result["response"]
        assert recovered.judge_result.score == sample_judge_result["score"]

    def test_preserves_timestamps(self, sample_gateway_request):
        """ProcessedRequest should preserve timestamps after serialization."""
        from src.objects.enums.processed_request import ProcessedRequest
        from src.objects.requests.gateway_request import GatewayRequest
        from src.objects.enums.request_stage import RequestStage
        from datetime import datetime

        processed = ProcessedRequest(
            request_id="test-123",
            gateway_request=GatewayRequest(**sample_gateway_request),
            stage=RequestStage.Gateway
        )

        original_created = processed.created_at
        original_updated = processed.updated_at

        json_str = processed.model_dump_json()
        recovered = ProcessedRequest.model_validate_json(json_str)

        assert isinstance(recovered.created_at, datetime)
        assert isinstance(recovered.updated_at, datetime)


class TestMessageSerialization:
    """Tests for message model serialization."""

    def test_inference_message_serialization(self, sample_gateway_request):
        """InferenceMessage should serialize with topic name."""
        from src.objects.messages.inference_message import InferenceMessage
        from src.objects.requests.gateway_request import GatewayRequest

        message = InferenceMessage(
            request_id="test-123",
            gateway_request=GatewayRequest(**sample_gateway_request)
        )

        json_str = message.model_dump_json()
        recovered = InferenceMessage.model_validate_json(json_str)

        assert recovered.topic_name == "inference"
        assert recovered.request_id == "test-123"
        assert recovered.gateway_request.prompt == sample_gateway_request["prompt"]

    def test_judge_message_serialization(
        self,
        sample_gateway_request,
        sample_inference_result
    ):
        """JudgeMessage should serialize with inference result."""
        from src.objects.messages.judge_message import JudgeMessage
        from src.objects.requests.gateway_request import GatewayRequest
        from src.objects.results.inference_result import InferenceResult

        message = JudgeMessage(
            request_id="test-123",
            gateway_request=GatewayRequest(**sample_gateway_request),
            inference_result=InferenceResult(**sample_inference_result)
        )

        json_str = message.model_dump_json()
        recovered = JudgeMessage.model_validate_json(json_str)

        assert recovered.topic_name == "judge"
        assert recovered.inference_result.response == sample_inference_result["response"]


class TestResultSerialization:
    """Tests for result model serialization."""

    def test_inference_result_serialization(self, sample_inference_result):
        """InferenceResult should preserve all fields after serialization."""
        from src.objects.results.inference_result import InferenceResult

        result = InferenceResult(**sample_inference_result)

        json_str = result.model_dump_json()
        recovered = InferenceResult.model_validate_json(json_str)

        assert recovered.response == sample_inference_result["response"]
        assert recovered.model == sample_inference_result["model"]
        assert recovered.latency_ms == sample_inference_result["latency_ms"]
        assert recovered.prompt_tokens == sample_inference_result["prompt_tokens"]
        assert recovered.completion_tokens == sample_inference_result["completion_tokens"]
        assert recovered.total_tokens == sample_inference_result["total_tokens"]

    def test_judge_result_serialization(self, sample_judge_result):
        """JudgeResult should preserve all fields including categories."""
        from src.objects.results.judge_result import JudgeResult

        result = JudgeResult(**sample_judge_result)

        json_str = result.model_dump_json()
        recovered = JudgeResult.model_validate_json(json_str)

        assert recovered.score == sample_judge_result["score"]
        assert recovered.reasoning == sample_judge_result["reasoning"]
        assert recovered.model == sample_judge_result["model"]
        assert recovered.categories["accuracy"] == sample_judge_result["categories"]["accuracy"]
        assert recovered.categories["relevance"] == sample_judge_result["categories"]["relevance"]


class TestFullLifecycleSerialization:
    """Tests for complete lifecycle serialization."""

    def test_full_lifecycle_data_integrity(
        self,
        sample_gateway_request,
        sample_inference_result,
        sample_judge_result
    ):
        """All models should maintain data integrity through complete lifecycle."""
        from src.objects.requests.gateway_request import GatewayRequest
        from src.objects.enums.processed_request import ProcessedRequest
        from src.objects.enums.request_stage import RequestStage
        from src.objects.results.inference_result import InferenceResult
        from src.objects.results.judge_result import JudgeResult
        from src.objects.messages.inference_message import InferenceMessage
        from src.objects.messages.judge_message import JudgeMessage

        # Step 1: Create gateway request
        gateway_request = GatewayRequest(**sample_gateway_request)
        gateway_json = gateway_request.model_dump_json()
        gateway_recovered = GatewayRequest.model_validate_json(gateway_json)

        # Step 2: Create inference message
        inference_message = InferenceMessage(
            request_id="lifecycle-test",
            gateway_request=gateway_recovered
        )
        inf_msg_json = inference_message.model_dump_json()
        inf_msg_recovered = InferenceMessage.model_validate_json(inf_msg_json)

        # Step 3: Create inference result
        inference_result = InferenceResult(**sample_inference_result)
        inf_result_json = inference_result.model_dump_json()
        inf_result_recovered = InferenceResult.model_validate_json(inf_result_json)

        # Step 4: Create judge message
        judge_message = JudgeMessage(
            request_id="lifecycle-test",
            gateway_request=inf_msg_recovered.gateway_request,
            inference_result=inf_result_recovered
        )
        judge_msg_json = judge_message.model_dump_json()
        judge_msg_recovered = JudgeMessage.model_validate_json(judge_msg_json)

        # Step 5: Create judge result
        judge_result = JudgeResult(**sample_judge_result)
        judge_result_json = judge_result.model_dump_json()
        judge_result_recovered = JudgeResult.model_validate_json(judge_result_json)

        # Step 6: Create completed processed request
        final_request = ProcessedRequest(
            request_id="lifecycle-test",
            gateway_request=judge_msg_recovered.gateway_request,
            stage=RequestStage.Completed,
            inference_result=judge_msg_recovered.inference_result,
            judge_result=judge_result_recovered
        )
        final_json = final_request.model_dump_json()
        final_recovered = ProcessedRequest.model_validate_json(final_json)

        # Verify data integrity throughout
        assert final_recovered.gateway_request.prompt == sample_gateway_request["prompt"]
        assert final_recovered.inference_result.response == sample_inference_result["response"]
        assert final_recovered.judge_result.score == sample_judge_result["score"]
        assert final_recovered.stage == RequestStage.Completed
