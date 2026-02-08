"""OpenAI LLM provider implementation."""
import time
from typing import Optional

from openai import OpenAI

from src.interfaces.llm_provider import LLMProvider, InferenceConfig, InferenceOutput
from src.objects.results.inference_result import InferenceResult

DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MODEL = "gpt-4o-mini"


class HealthCheckError(Exception):
    """Raised when OpenAI API health check fails."""
    pass


class OpenAIClient(LLMProvider):
    """OpenAI LLM provider implementation."""

    def __init__(self, api_key: str):
        self._client = OpenAI(api_key=api_key)
        self._api_key = api_key

    def generate(self, prompt: str, config: InferenceConfig) -> InferenceOutput:
        messages = []
        if config.system_prompt:
            messages.append({"role": "system", "content": config.system_prompt})
        messages.append({"role": "user", "content": prompt})

        start_time = time.time()

        response = self._client.chat.completions.create(
            model=config.model,
            messages=messages,
            max_tokens=config.max_tokens or DEFAULT_MAX_TOKENS,
            temperature=config.temperature
        )

        latency_ms = (time.time() - start_time) * 1000

        usage = response.usage
        return InferenceOutput(
            response=response.choices[0].message.content,
            model=response.model,
            latency_ms=latency_ms,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0
        )

    def check_health(self) -> None:
        try:
            self._client.models.list()
        except Exception as e:
            raise HealthCheckError(f"OpenAI API unreachable: {e}") from e

    def is_healthy(self) -> bool:
        try:
            self.check_health()
            return True
        except HealthCheckError:
            return False

    def _chat_completion(
        self,
        prompt: str,
        config: Optional[InferenceConfig] = None
    ) -> InferenceResult:
        if config is None:
            config = InferenceConfig(
                model=DEFAULT_MODEL,
                temperature=DEFAULT_TEMPERATURE,
                max_tokens=DEFAULT_MAX_TOKENS
            )
        output = self.generate(prompt, config)
        return InferenceResult(
            response=output.response,
            model=output.model,
            latency_ms=output.latency_ms,
            prompt_tokens=output.prompt_tokens,
            completion_tokens=output.completion_tokens,
            total_tokens=output.total_tokens
        )
