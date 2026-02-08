from typing import Optional, Any

from pydantic import BaseModel, ConfigDict


class HistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: str
    prompt: str
    target_model: str
    judge_model: str
    inference_response: Optional[str] = None
    inference_latency_ms: Optional[float] = None
    inference_tokens: Optional[int] = None
    judge_score: Optional[float] = None
    judge_reasoning: Optional[str] = None
    judge_categories: Optional[Any] = None
    judge_latency_ms: Optional[float] = None
    status: str
    error_message: Optional[str] = None
    created_at: str
    completed_at: str

    @classmethod
    def from_orm(cls, history) -> "HistoryResponse":
        return cls(
            id=history.id,
            request_id=history.request_id,
            prompt=history.prompt,
            target_model=history.target_model,
            judge_model=history.judge_model,
            inference_response=history.inference_response,
            inference_latency_ms=history.inference_latency_ms,
            inference_tokens=history.inference_tokens,
            judge_score=history.judge_score,
            judge_reasoning=history.judge_reasoning,
            judge_categories=history.judge_categories,
            judge_latency_ms=history.judge_latency_ms,
            status=history.status,
            error_message=history.error_message,
            created_at=history.created_at.isoformat() if history.created_at else None,
            completed_at=history.completed_at.isoformat() if history.completed_at else None,
        )
