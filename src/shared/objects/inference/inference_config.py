"""Inference configuration value object."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class InferenceConfig:
    """Configuration for LLM inference."""
    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
