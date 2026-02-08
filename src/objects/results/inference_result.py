from typing import Optional

from pydantic import BaseModel


class InferenceResult(BaseModel):
    response: str
    model: str
    latency_ms: float
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
