"""OpenAI LLM provider implementation."""
import time
from typing import Optional

from openai import OpenAI

from src.shared.interfaces.inference.inference_provider import InferenceProvider
from src.shared.objects.inference.inference_config import InferenceConfig
from src.shared.objects.inference.inference_result import InferenceResult
from src.shared.observability.logs.logger import Logger

DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MODEL = "gpt-4o-mini"


class OpenAIProvider(InferenceProvider):
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._api_key = api_key
        self._logger = Logger()

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
            temperature=config.temperature
        )

        latency_ms = (time.time() - start_time) * 1000

        usage = response.usage

        if usage is None:
            self._logger.error("Usage was not provided")

        return InferenceResult(
            response=response.choices[0].message.content,
            model=response.model,
            latency_ms=latency_ms,
            prompt_tokens=usage.prompt_tokens if usage else None,
            completion_tokens=usage.completion_tokens if usage else None,
            total_tokens=usage.total_tokens if usage else None
        )

    def check_health(self) -> None:
        try:
            self._client.models.list()
        except Exception as e:
            self._logger.error("Open AI API is unreachable")
            raise e

    def is_healthy(self) -> bool:
        try:
            self.check_health()
            return True
        except Exception as e:
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
        return self.run_inference(prompt, config)
