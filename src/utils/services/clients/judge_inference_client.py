"""HTTP client for judge inference service."""
import time
from functools import lru_cache
from typing import Any, Dict

import httpx

from src.interfaces.judge_gateway import JudgeGateway
from src.utils.services.aws.appconfig_service import get_config_service


class JudgeInferenceClient(JudgeGateway):
    """HTTP client for judge inference service."""

    def __init__(self):
        appconfig = get_config_service()
        host = appconfig.get("services.judge_inference.host", "judge-inference-service")
        port = appconfig.get("services.judge_inference.port", 8003)
        self._base_url = f"http://{host}:{port}"
        self._client = httpx.Client(timeout=120.0)

    def judge(
        self,
        original_prompt: str,
        model_response: str,
        model: str = "qwen2.5:latest"
    ) -> Dict[str, Any]:
        start_time = time.time()

        # TODO: Replace with actual HTTP call to judge inference service
        # response = self._client.post(
        #     f"{self._base_url}/judge",
        #     json={
        #         "original_prompt": original_prompt,
        #         "model_response": model_response,
        #         "model": model
        #     }
        # )
        # response.raise_for_status()
        # result = response.json()

        latency_ms = (time.time() - start_time) * 1000

        return {
            "score": 0.5,
            "reasoning": "Placeholder: Judge inference service not yet implemented",
            "categories": {
                "relevance": 0.5,
                "accuracy": 0.5,
                "helpfulness": 0.5,
                "safety": 1.0
            },
            "model": model,
            "latency_ms": latency_ms
        }

    def is_healthy(self) -> bool:
        try:
            response = self._client.get(f"{self._base_url}/health")
            return response.status_code == 200
        except Exception:
            return False


@lru_cache(maxsize=1)
def get_judge_gateway() -> JudgeInferenceClient:
    """Get the singleton JudgeInferenceClient instance."""
    return JudgeInferenceClient()
