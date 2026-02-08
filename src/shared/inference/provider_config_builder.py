"""Provider config builder - maps config strings to provider configs."""
from src.shared.interfaces.inference_provider_config import InferenceProviderConfig
from src.shared.inference.provider_configs.google_provider_config import GoogleProviderConfig
from src.shared.inference.provider_configs.openai_provider_config import OpenAIProviderConfig
from src.shared.inference.provider_configs.ollama_provider_config import OllamaProviderConfig

_PROVIDER_TYPE_MAP = {
    "openai": OpenAIProviderConfig,
    "google": GoogleProviderConfig,
    "ollama": OllamaProviderConfig,
}

_MODEL_DEFAULTS = {
    "openai": "gpt-4o-mini",
    "google": "gemini-2.0-flash",
    "ollama": "llama3",
}


def build_provider_config(config_service, prefix: str) -> InferenceProviderConfig:
    """Build an InferenceProviderConfig from application config.

    Reads keys under the given prefix:
      - {prefix}.provider_type  (e.g. "google", "openai", "ollama")
      - {prefix}.model          (model name override)
      - {prefix}.api_key        (remote providers only)
      - {prefix}.base_url       (optional endpoint override)
    """
    provider_type = config_service.get(f"{prefix}.provider_type", "google")
    model = config_service.get(f"{prefix}.model", _MODEL_DEFAULTS.get(provider_type, "gpt-4o-mini"))

    config_cls = _PROVIDER_TYPE_MAP.get(provider_type)
    if config_cls is None:
        raise ValueError(f"Unknown provider_type: {provider_type!r}. Supported: {list(_PROVIDER_TYPE_MAP)}")

    if provider_type == "ollama":
        base_url = config_service.get(f"{prefix}.base_url", "http://localhost:11434/v1")
        return OllamaProviderConfig(model_name=model, base_url=base_url)

    api_key = config_service.get(f"{prefix}.api_key", "")

    if provider_type == "openai":
        base_url = config_service.get(f"{prefix}.base_url", "https://api.openai.com/v1")
        return OpenAIProviderConfig(api_key=api_key, model_name=model, base_url=base_url)

    return GoogleProviderConfig(api_key=api_key, model_name=model)
