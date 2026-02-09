"""Google Gemini LLM provider implementation."""
import time
from typing import Optional

from google import genai
from google.genai import types

from src.shared.interfaces.inference.inference_provider import InferenceProvider
from src.shared.objects.inference.inference_config import InferenceConfig
from src.shared.objects.inference.inference_result import InferenceResult
from src.shared.observability.logs.logger import Logger


class GoogleProvider(InferenceProvider):
    def __init__(self, api_key: str):
        self._client = genai.Client(api_key=api_key)
        self._api_key = api_key
        self._logger = Logger()

    def run_inference(self, prompt: str, config: InferenceConfig) -> InferenceResult:
        content_config = types.GenerateContentConfig(
            max_output_tokens=config.max_tokens or 4096,
            temperature=config.temperature,
        )

        if config.system_prompt:
            content_config.system_instruction = config.system_prompt

        start_time = time.time()

        response = self._client.models.generate_content(
            model=config.model,
            contents=prompt,
            config=content_config
        )

        latency_ms = (time.time() - start_time) * 1000

        usage_metadata = response.usage_metadata
        if usage_metadata is None:
            self._logger.error("Usage metadata was not provided")

        return InferenceResult(
            response=response.text,
            model=config.model,
            latency_ms=latency_ms,
            prompt_tokens=usage_metadata.prompt_token_count if usage_metadata else None,
            completion_tokens=usage_metadata.candidates_token_count if usage_metadata else None,
            total_tokens=usage_metadata.total_token_count if usage_metadata else None
        )

    def is_healthy(self) -> bool:
        try:
            return True
        except Exception:
            return False

    def _chat_completion(
        self,
        prompt: str,
        model: str = "gemini-2.0-flash",
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7
    ) -> InferenceResult:
        config = InferenceConfig(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt
        )
        return self.run_inference(prompt, config)
