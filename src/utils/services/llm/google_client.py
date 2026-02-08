"""Google Gemini LLM provider implementation."""
import time
from typing import Optional

from google import genai
from google.genai import types

from src.interfaces.llm_provider import LLMProvider, InferenceConfig, InferenceOutput


class GoogleClient(LLMProvider):
    """Google Gemini LLM provider implementation."""

    def __init__(self, api_key: str):
        self._client = genai.Client(api_key=api_key)
        self._api_key = api_key

    def generate(self, prompt: str, config: InferenceConfig) -> InferenceOutput:
        gen_config = types.GenerateContentConfig(
            max_output_tokens=config.max_tokens or 4096,
            temperature=config.temperature,
        )

        if config.system_prompt:
            gen_config.system_instruction = config.system_prompt

        start_time = time.time()

        response = self._client.models.generate_content(
            model=config.model,
            contents=prompt,
            config=gen_config
        )

        latency_ms = (time.time() - start_time) * 1000

        usage_metadata = response.usage_metadata
        return InferenceOutput(
            response=response.text,
            model=config.model,
            latency_ms=latency_ms,
            prompt_tokens=usage_metadata.prompt_token_count if usage_metadata else 0,
            completion_tokens=usage_metadata.candidates_token_count if usage_metadata else 0,
            total_tokens=usage_metadata.total_token_count if usage_metadata else 0
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
    ) -> InferenceOutput:
        config = InferenceConfig(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt
        )
        return self.generate(prompt, config)
