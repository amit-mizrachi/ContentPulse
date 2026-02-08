"""Ollama local inference provider implementation."""
import time

from src.shared.interfaces.llm_provider import LLMProvider
from src.shared.objects.inference.inference_config import InferenceConfig
from src.shared.objects.inference.inference_result import InferenceResult

DEFAULT_MAX_TOKENS = 4096

# TODO: Replace the OpenAI-compatible client with a native Ollama SDK
#  (e.g. ollama-python) once we settle on the local inference protocol.
#  The current implementation piggybacks on Ollama's OpenAI-compatible
#  endpoint (/v1/chat/completions), which works but ties us to that
#  compatibility layer. A native client would give us access to
#  Ollama-specific features: model pulling, streaming, keep-alive
#  control, and raw /api/generate for non-chat workloads.


class OllamaProvider(LLMProvider):
    """Provider for local inference via Ollama."""

    def __init__(self, base_url: str = "http://localhost:11434/v1"):
        from openai import OpenAI

        self._base_url = base_url
        self._client = OpenAI(api_key="not-needed", base_url=base_url)

    def run_inference(self, prompt: str, config: InferenceConfig) -> InferenceResult:
        messages = []
        if config.system_prompt:
            messages.append({"role": "system", "content": config.system_prompt})
        messages.append({"role": "user", "content": prompt})

        start_time = time.time()

        response = self._client.chat.completions.create(
            model=config.model,
            messages=messages,
            max_tokens=config.max_tokens or DEFAULT_MAX_TOKENS,
            temperature=config.temperature,
        )

        latency_ms = (time.time() - start_time) * 1000

        usage = response.usage
        return InferenceResult(
            response=response.choices[0].message.content,
            model=response.model,
            latency_ms=latency_ms,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
        )

    def is_healthy(self) -> bool:
        try:
            self._client.models.list()
            return True
        except Exception:
            return False
