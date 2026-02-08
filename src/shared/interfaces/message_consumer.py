from abc import ABC, abstractmethod


class AsyncMessageConsumer(ABC):
    """Interface for consuming messages asynchronically from queues/topics."""

    @abstractmethod
    async def start(self) -> None:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass
