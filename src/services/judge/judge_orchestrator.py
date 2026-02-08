"""Judge Orchestrator - orchestrates the judgment workflow and persistence."""
from datetime import datetime
from typing import Any, Dict

from src.interfaces.message_handler import MessageHandler
from src.interfaces.state_repository import StateRepository
from src.interfaces.persistence_gateway import PersistenceGateway
from src.interfaces.judge_gateway import JudgeGateway
from src.objects.enums.processed_request import ProcessedRequest
from src.objects.enums.request_stage import RequestStage
from src.objects.messages.judge_message import JudgeMessage
from src.objects.results.judge_result import JudgeResult
from src.utils.observability.logs.logger import Logger


class JudgeOrchestrator(MessageHandler):
    """Orchestrates the evaluation of inference results and final persistence."""

    def __init__(
        self,
        state_repository: StateRepository,
        persistence_gateway: PersistenceGateway,
        judge_gateway: JudgeGateway,
    ):
        self._logger = Logger()
        self._state_repository = state_repository
        self._persistence_gateway = persistence_gateway
        self._judge_gateway = judge_gateway

    def handle(self, raw_message, *args, **kwargs) -> bool:
        judge_message = JudgeMessage.model_validate(raw_message)
        return self._orchestrate_judgment(judge_message)

    def _orchestrate_judgment(self, message: JudgeMessage) -> bool:
        request_id = message.request_id

        try:
            self._update_stage(request_id, RequestStage.Judge)

            judge_result_data = self._perform_evaluation(message)
            judge_result = JudgeResult.model_validate(judge_result_data)
            self._complete_request(request_id, judge_result)

            self._archive_request(request_id)

            self._logger.info(f"Judgment completed for {request_id}, score: {judge_result.score}")
            return True

        except Exception as e:
            self._handle_failure(request_id, e)
            return False

    def _perform_evaluation(self, message: JudgeMessage) -> Dict[str, Any]:
        return self._judge_gateway.judge(
            original_prompt=message.get_original_prompt(),
            model_response=message.get_inference_response(),
            model=message.get_judge_model_identifier()
        )

    def _complete_request(self, request_id: str, result: JudgeResult):
        self._state_repository.update(request_id, {
            "judge_result": result.model_dump(),
            "stage": RequestStage.Completed.value
        })

    def _archive_request(self, request_id: str):
        state_data = self._state_repository.get(request_id)
        if state_data:
            processed_request = ProcessedRequest.model_validate(state_data)
            history_data = self._map_to_history(processed_request)
            self._persistence_gateway.create_history(history_data)

    def _update_stage(self, request_id: str, stage: RequestStage):
        self._state_repository.update(request_id, {"stage": stage.value})

    def _handle_failure(self, request_id: str, error: Exception):
        self._logger.error(f"Judgment failed for {request_id}: {error}")

        self._state_repository.update(request_id, {
            "stage": RequestStage.Failed.value,
            "error_message": str(error)
        })

        try:
            self._archive_request(request_id)
        except Exception as persist_error:
            self._logger.error(f"Failed to persist failure for {request_id}: {persist_error}")

    @staticmethod
    def _map_to_history(request: ProcessedRequest) -> Dict[str, Any]:
        history = {
            "request_id": request.request_id,
            "prompt": request.get_prompt(),
            "target_model": request.get_target_model_name(),
            "judge_model": request.get_judge_model_identifier(),
            "status": request.stage.value,
            "error_message": request.error_message,
            "created_at": request.created_at.isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
        }

        history.update(request.get_inference_history_data())
        history.update(request.get_judge_history_data())

        return history
