"""Inference Orchestrator - orchestrates the inference workflow."""
from src.interfaces.llm_provider import LLMProviderFactory, InferenceConfig
from src.interfaces.message_handler import MessageHandler
from src.interfaces.message_publisher import MessagePublisher
from src.interfaces.state_repository import StateRepository
from src.objects.enums.request_stage import RequestStage
from src.objects.messages.inference_message import InferenceMessage
from src.objects.messages.judge_message import JudgeMessage
from src.objects.results.inference_result import InferenceResult
from src.utils.observability.logs.logger import Logger


class InferenceOrchestrator(MessageHandler):
    """Orchestrates the lifecycle of an inference request: Status update -> Model Call -> Result Publish."""

    def __init__(
        self,
        state_repository: StateRepository,
        message_publisher: MessagePublisher,
        llm_factory: LLMProviderFactory,
        judge_topic: str,
    ):
        self._logger = Logger()
        self._state_repository = state_repository
        self._message_publisher = message_publisher
        self._llm_factory = llm_factory
        self._judge_topic = judge_topic

    def handle(self, raw_message, *args, **kwargs) -> bool:
        inference_message = InferenceMessage.model_validate(raw_message)
        return self._orchestrate_inference(inference_message)

    def _orchestrate_inference(self, message: InferenceMessage) -> bool:
        request_id = message.request_id

        try:
            self._update_stage(request_id, RequestStage.Inference)

            result = self._execute_inference(message)
            self._save_result(request_id, result)

            self._notify_judge(request_id, message, result)

            self._logger.info(f"Completed inference for {request_id}")
            return True

        except Exception as e:
            self._handle_failure(request_id, e)
            return False

    def _execute_inference(self, message: InferenceMessage) -> InferenceResult:
        gateway_req = message.gateway_request
        target_model = gateway_req.target_model.name
        api_key = gateway_req.api_key.get_secret_value()

        provider = self._llm_factory.create_provider(target_model, api_key)
        actual_model_name = self._llm_factory.resolve_model_name(target_model)

        config = InferenceConfig(model=actual_model_name)
        output = provider.generate(prompt=gateway_req.prompt, config=config)
        return InferenceResult(
            response=output.response,
            model=output.model,
            latency_ms=output.latency_ms,
            prompt_tokens=output.prompt_tokens,
            completion_tokens=output.completion_tokens,
            total_tokens=output.total_tokens
        )

    def _notify_judge(self, request_id: str, message: InferenceMessage, result: InferenceResult):
        judge_message = JudgeMessage(
            request_id=request_id,
            gateway_request=message.gateway_request,
            inference_result=result
        )
        self._message_publisher.publish(self._judge_topic, judge_message.model_dump_json())

    def _update_stage(self, request_id: str, stage: RequestStage):
        self._state_repository.update(request_id, {"stage": stage.value})

    def _save_result(self, request_id: str, result: InferenceResult):
        self._state_repository.update(request_id, {
            "inference_result": result.model_dump()
        })

    def _handle_failure(self, request_id: str, error: Exception):
        self._logger.error(f"Inference failed for {request_id}: {error}")
        self._state_repository.update(request_id, {
            "stage": RequestStage.Failed.value,
            "error_message": str(error)
        })
