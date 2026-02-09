"""State Repository Interface - defines the contract for request state persistence."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class RequestStateRepository(ABC):
    @abstractmethod
    def create(self, request_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get(self, request_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def update(self, request_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def delete(self, request_id: str) -> bool:
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        pass
