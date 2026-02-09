"""Inference result value object."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class InferenceResult:
    response: str
    model: str
    prompt_tokens: int
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    latency_ms: Optional[float] = None
