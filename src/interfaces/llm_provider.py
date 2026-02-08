"""LLM Provider interface."""
from abc import ABC, abstractmethod

from src.objects.inference.inference_config import InferenceConfig
from src.objects.inference.inference_output import InferenceOutput


class LLMProvider(ABC):
    """Interface for LLM inference providers."""

    @abstractmethod
    def run_inference(self, prompt: str, config: InferenceConfig) -> InferenceOutput:
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        pass
