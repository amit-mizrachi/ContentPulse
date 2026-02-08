"""Inference output value object."""
from dataclasses import dataclass


@dataclass
class InferenceOutput:
    """Output from LLM inference."""
    response: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float
