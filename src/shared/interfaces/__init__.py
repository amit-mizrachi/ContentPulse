# Domain Interfaces (Ports)
# These abstract base classes define contracts that infrastructure must implement
# Following the Dependency Inversion Principle (DIP)

from src.shared.interfaces.state_repository import StateRepository
from src.shared.interfaces.message_publisher import MessagePublisher
from src.shared.interfaces.message_consumer import AsyncMessageConsumer
from src.shared.interfaces.llm_provider import LLMProvider
from src.shared.interfaces.inference_provider_config import InferenceProviderConfig
from src.shared.interfaces.article_store import ArticleStore
from src.shared.interfaces.content_source import ContentSource
from src.shared.interfaces.message_handler import MessageHandler
from src.shared.interfaces.message_dispatcher import MessageDispatcher

__all__ = [
    "StateRepository",
    "MessagePublisher",
    "AsyncMessageConsumer",
    "LLMProvider",
    "InferenceProviderConfig",
    "ArticleStore",
    "ContentSource",
    "MessageHandler",
    "MessageDispatcher",
]
