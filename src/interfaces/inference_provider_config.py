"""Inference Provider Config interface."""
from abc import ABC, abstractmethod

from src.interfaces.llm_provider import LLMProvider
from src.objects.enums.inference_mode import InferenceMode


class InferenceProviderConfig(ABC):
    """Abstract config that knows how to create its own LLM provider."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def model(self) -> str:
        pass

    @property
    @abstractmethod
    def endpoint(self) -> str:
        pass

    @property
    @abstractmethod
    def inference_mode(self) -> InferenceMode:
        pass

    @abstractmethod
    def create_provider(self) -> LLMProvider:
        pass
