"""Persistence Gateway Interface - defines the contract for history persistence."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class PersistenceGateway(ABC):
    """Interface for persisting request history to long-term storage."""

    @abstractmethod
    def create_history(self, history_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_history(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_history_by_request_id(self, request_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        pass
