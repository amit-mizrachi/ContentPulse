"""LLM Provider Interface - defines the contract for LLM inference."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class InferenceConfig:
    """Configuration for LLM inference."""
    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None


@dataclass
class InferenceOutput:
    """Output from LLM inference."""
    response: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float


class LLMProvider(ABC):
    """Interface for LLM inference providers."""

    @abstractmethod
    def generate(self, prompt: str, config: InferenceConfig) -> InferenceOutput:
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        pass


class LLMProviderFactory(ABC):
    """Factory interface for creating LLM providers."""

    @abstractmethod
    def create_provider(self, provider_name: str, api_key: str) -> LLMProvider:
        pass

    @abstractmethod
    def resolve_model_name(self, provider_name: str) -> str:
        pass
