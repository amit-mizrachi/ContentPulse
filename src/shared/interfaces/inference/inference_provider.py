"""LLM Provider interface."""
from abc import ABC, abstractmethod

from src.shared.objects.inference.inference_config import InferenceConfig
from src.shared.objects.inference.inference_result import InferenceResult


class InferenceProvider(ABC):
    @abstractmethod
    def run_inference(self, prompt: str, config: InferenceConfig) -> InferenceResult:
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        pass
