"""Google provider configuration."""
from dataclasses import dataclass

from src.interfaces.inference_provider_config import InferenceProviderConfig
from src.interfaces.llm_provider import LLMProvider
from src.objects.enums.inference_mode import InferenceMode
from src.utils.services.inference.providers.google_provider import GoogleProvider


@dataclass
class GoogleProviderConfig(InferenceProviderConfig):
    """Config for Google Gemini inference."""
    api_key: str
    model_name: str

    @property
    def provider_name(self) -> str:
        return "google"

    @property
    def model(self) -> str:
        return self.model_name

    @property
    def endpoint(self) -> str:
        return "https://generativelanguage.googleapis.com"

    @property
    def inference_mode(self) -> InferenceMode:
        return InferenceMode.REMOTE

    def create_provider(self) -> LLMProvider:
        return GoogleProvider(api_key=self.api_key)
