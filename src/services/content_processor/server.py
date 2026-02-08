"""Content Processor Service - consumes raw content and enriches via LLM."""
import asyncio
import signal

from src.services.content_processor.content_processor_orchestrator import ContentProcessorOrchestrator
from src.utils.observability.logs.logger import Logger
from src.utils.queue.messaging_factory import get_message_consumer
from src.utils.queue.queue_message_handler import ThreadPoolMessageDispatcher
from src.utils.services.aws.appconfig_service import get_config_service
from src.utils.services.clients.mongodb_client import get_content_repository
from src.utils.services.config.health import start_health_server_background
from src.utils.services.config.ports import get_service_port
from src.utils.services.llm.llm_provider_factory import DefaultLLMProviderFactory

logger = Logger()

SERVICE_PORT_KEY = "services.content_processor.port"
DEFAULT_PORT = 8003


def create_content_processor_orchestrator() -> ContentProcessorOrchestrator:
    config_service = get_config_service()
    return ContentProcessorOrchestrator(
        content_repository=get_content_repository(),
        llm_factory=DefaultLLMProviderFactory(),
        processing_model=config_service.get("content_processor.model", "Gemini-Flash"),
        api_key=config_service.get("content_processor.api_key", ""),
    )


async def main():
    logger.info("Starting Content Processor Service")

    orchestrator = create_content_processor_orchestrator()
    handler = ThreadPoolMessageDispatcher(orchestrator)
    consumer = get_message_consumer(handler, service_name="content_processor")

    port = get_service_port(SERVICE_PORT_KEY, default=DEFAULT_PORT)
    logger.info(f"Starting health server on port {port}")
    health_task = start_health_server_background(
        service_name="Content Processor Service",
        appconfig_key=SERVICE_PORT_KEY,
        default_port=DEFAULT_PORT
    )

    loop = asyncio.get_running_loop()

    def signal_handler():
        logger.info("Received shutdown signal")
        health_task.cancel()
        asyncio.create_task(consumer.close())

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    await consumer.start()


if __name__ == "__main__":
    asyncio.run(main())
