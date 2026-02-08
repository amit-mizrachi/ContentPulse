"""Judge Gateway Interface - defines the contract for judge inference operations."""
from abc import ABC, abstractmethod
from typing import Any, Dict


class JudgeGateway(ABC):
    """Interface for judge inference operations."""

    @abstractmethod
    def judge(
        self,
        original_prompt: str,
        model_response: str,
        model: str = "qwen2.5:latest"
    ) -> Dict[str, Any]:
        """Returns dict with: score, reasoning, categories, model, latency_ms."""
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        pass
