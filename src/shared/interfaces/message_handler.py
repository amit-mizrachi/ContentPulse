"""MessageHandler Interface - defines the contract for processing queue messages."""
from abc import ABC, abstractmethod


class MessageHandler(ABC):
    """Interface for handling raw queue messages."""

    @abstractmethod
    def handle(self, raw_message, *args, **kwargs) -> bool:
        pass
