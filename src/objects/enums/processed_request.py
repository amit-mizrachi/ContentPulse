from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from src.objects.requests.gateway_request import GatewayRequest
from src.objects.enums.request_stage import RequestStage
from src.objects.results.inference_result import InferenceResult
from src.objects.results.judge_result import JudgeResult


class ProcessedRequest(BaseModel):
    """
    Data structure representing the state of a request through the pipeline.
    """
    request_id: str
    gateway_request: GatewayRequest
    stage: RequestStage
    inference_result: Optional[InferenceResult] = None
    judge_result: Optional[JudgeResult] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def get_prompt(self) -> str:
        return self.gateway_request.prompt

    def get_target_model_name(self) -> str:
        return self.gateway_request.get_target_model_name()

    def get_judge_model_identifier(self) -> str:
        return self.gateway_request.get_judge_model_identifier()

    def get_inference_history_data(self) -> dict:
        if not self.inference_result:
            return {}
        return {
            "inference_response": self.inference_result.response,
            "inference_latency_ms": self.inference_result.latency_ms,
            "inference_tokens": self.inference_result.total_tokens,
        }

    def get_judge_history_data(self) -> dict:
        if not self.judge_result:
            return {}
        return {
            "judge_score": self.judge_result.score,
            "judge_reasoning": self.judge_result.reasoning,
            "judge_categories": self.judge_result.categories,
            "judge_latency_ms": self.judge_result.latency_ms,
        }
