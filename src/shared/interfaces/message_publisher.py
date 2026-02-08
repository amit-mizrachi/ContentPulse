"""Message Publisher Interface - defines the contract for publishing messages."""
from abc import ABC, abstractmethod


class MessagePublisher(ABC):
    """Interface for publishing messages to topics/queues."""

    @abstractmethod
    def publish(self, topic_name: str, message: str) -> bool:
        pass
