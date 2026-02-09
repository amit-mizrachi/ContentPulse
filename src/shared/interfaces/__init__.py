# Domain Interfaces (Ports)
# These abstract base classes define contracts that infrastructure must implement
# Following the Dependency Inversion Principle (DIP)

from src.shared.interfaces.repositories.request_state_repository import RequestStateRepository
from src.shared.interfaces.messaging.message_publisher import MessagePublisher
from src.shared.interfaces.messaging.message_consumer import AsyncMessageConsumer
from src.shared.interfaces.inference.inference_provider import InferenceProvider
from src.shared.interfaces.inference.inference_provider_config import InferenceProviderConfig
from src.shared.interfaces.repositories.article_repository import ArticleRepository
from src.shared.interfaces.content_source import ContentSource
from src.shared.interfaces.messaging.message_handler import MessageHandler
from src.shared.interfaces.messaging.message_dispatcher import MessageDispatcher

__all__ = [
    "RequestStateRepository",
    "MessagePublisher",
    "AsyncMessageConsumer",
    "InferenceProvider",
    "InferenceProviderConfig",
    "ArticleRepository",
    "ContentSource",
    "MessageHandler",
    "MessageDispatcher",
]
