"""Inference result value object."""
from dataclasses import dataclass


@dataclass
class InferenceResult:
    """Result from LLM inference."""
    response: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float
