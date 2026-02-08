from typing import Optional, Dict, Any

from pydantic import BaseModel


class JudgeResult(BaseModel):
    score: float
    reasoning: str
    categories: Optional[Dict[str, Any]] = None
    model: str
    latency_ms: float
