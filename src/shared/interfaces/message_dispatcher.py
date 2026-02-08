"""MessageDispatcher Interface - defines the contract for concurrent message dispatch."""
from abc import ABC, abstractmethod
from concurrent.futures import Future
from typing import Any


class MessageDispatcher(ABC):
    """Interface for dispatching raw queue messages to a worker pool."""

    @abstractmethod
    def submit(self, raw_message: Any, *args, **kwargs) -> Future:
        pass

    @property
    @abstractmethod
    def max_worker_count(self) -> int:
        pass

    @abstractmethod
    def close(self, *args, **kwargs) -> None:
        pass
