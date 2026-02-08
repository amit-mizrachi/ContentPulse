from typing import Optional

from pydantic import BaseModel


class HistoryCreateRequest(BaseModel):
    request_id: str
    prompt: str
    target_model: str
    judge_model: str
    inference_response: Optional[str] = None
    inference_latency_ms: Optional[float] = None
    inference_tokens: Optional[int] = None
    judge_score: Optional[float] = None
    judge_reasoning: Optional[str] = None
    judge_categories: Optional[dict] = None
    judge_latency_ms: Optional[float] = None
    status: str
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
