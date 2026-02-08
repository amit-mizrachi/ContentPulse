"""LLM Provider Factory - creates LLM provider instances."""
from typing import Dict, Set

from src.interfaces.llm_provider import LLMProvider, LLMProviderFactory


class DefaultLLMProviderFactory(LLMProviderFactory):
    """Factory for creating LLM provider instances.

    Note: This is NOT a singleton because LLM providers are created
    per-request with different API keys.
    """

    _GOOGLE_MODELS: Set[str] = {
        "Gemini",
        "Gemini-Flash",
        "Gemini-2.5-Flash",
        "Gemini-Pro",
    }

    _MODEL_MAPPING: Dict[str, str] = {
        "ChatGPT": "gpt-4o-mini",
        "GPT-4": "gpt-4",
        "GPT-4o": "gpt-4o",
        "GPT-4o-mini": "gpt-4o-mini",
        "Gemini": "gemini-2.0-flash",
        "Gemini-Flash": "gemini-2.0-flash",
        "Gemini-2.5-Flash": "gemini-2.5-flash",
        "Gemini-Pro": "gemini-2.5-pro",
    }

    def create_provider(self, provider_name: str, api_key: str) -> LLMProvider:
        # Lazy imports to avoid requiring all provider dependencies at import time
        if provider_name in self._GOOGLE_MODELS:
            from src.utils.services.llm.google import GoogleClient
            return GoogleClient(api_key=api_key)
        from src.utils.services.llm.openai import OpenAIClient
        return OpenAIClient(api_key=api_key)

    def resolve_model_name(self, provider_name: str) -> str:
        return self._MODEL_MAPPING.get(provider_name, "gpt-4o-mini")

    def is_google_model(self, provider_name: str) -> bool:
        return provider_name in self._GOOGLE_MODELS

    def get_supported_models(self) -> Dict[str, str]:
        return self._MODEL_MAPPING.copy()
