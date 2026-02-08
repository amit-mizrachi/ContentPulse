"""OpenAI provider configuration."""
from dataclasses import dataclass

from src.interfaces.inference_provider_config import InferenceProviderConfig
from src.interfaces.llm_provider import LLMProvider
from src.objects.enums.inference_mode import InferenceMode
from src.utils.services.inference.providers.openai_provider import OpenAIProvider


@dataclass
class OpenAIProviderConfig(InferenceProviderConfig):
    """Config for OpenAI-compatible remote inference."""
    api_key: str
    model_name: str
    base_url: str = "https://api.openai.com/v1"

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model(self) -> str:
        return self.model_name

    @property
    def endpoint(self) -> str:
        return self.base_url

    @property
    def inference_mode(self) -> InferenceMode:
        return InferenceMode.REMOTE

    def create_provider(self) -> LLMProvider:
        return OpenAIProvider(api_key=self.api_key, base_url=self.base_url)
