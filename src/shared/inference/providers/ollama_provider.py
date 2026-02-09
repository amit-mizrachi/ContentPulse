"""Ollama local inference provider implementation."""
import time
from http.client import UnimplementedFileMode

from src.shared.interfaces.inference.inference_provider import InferenceProvider
from src.shared.objects.inference.inference_config import InferenceConfig
from src.shared.objects.inference.inference_result import InferenceResult

# TODO: Implement after we establish deployment plan


class OllamaProvider(InferenceProvider):
    def __init__(self, base_url: str = "http://localhost:11434/v1"):
        raise NotImplemented

    def run_inference(self, prompt: str, config: InferenceConfig) -> InferenceResult:
        raise NotImplemented

    def is_healthy(self) -> bool:
        raise NotImplemented
