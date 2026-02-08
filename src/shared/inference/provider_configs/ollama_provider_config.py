"""Ollama local inference provider configuration."""
from dataclasses import dataclass

from src.shared.interfaces.inference_provider_config import InferenceProviderConfig
from src.shared.interfaces.llm_provider import LLMProvider
from src.shared.objects.enums.inference_mode import InferenceMode
from src.shared.inference.providers.ollama_provider import OllamaProvider


@dataclass
class OllamaProviderConfig(InferenceProviderConfig):
    """Config for Ollama local inference."""
    model_name: str
    base_url: str = "http://localhost:11434/v1"

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model(self) -> str:
        return self.model_name

    @property
    def endpoint(self) -> str:
        return self.base_url

    @property
    def inference_mode(self) -> InferenceMode:
        return InferenceMode.LOCAL

    def create_provider(self) -> LLMProvider:
        return OllamaProvider(base_url=self.base_url)
