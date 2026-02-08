"""Content Processor Service - consumes raw content and enriches via LLM."""
import asyncio
import signal

from src.services.content_processor.content_processor_orchestrator import ContentProcessorOrchestrator
from src.shared.observability.logs.logger import Logger
from src.shared.observability.traces.tracer import Tracer
from src.shared.messaging.messaging_factory import get_message_consumer
from src.shared.messaging.thread_pool_message_dispatcher import ThreadPoolMessageDispatcher
from src.shared.aws.appconfig_service import get_config_service
from src.shared.storage.mongodb_client import get_content_repository
from src.shared.config.health import start_health_server_background
from src.shared.config.ports import get_service_port
from src.shared.inference.provider_config_builder import build_provider_config

logger = Logger()
tracer = Tracer()

SERVICE_PORT_KEY = "services.content_processor.port"
DEFAULT_PORT = 8003


def create_content_processor_orchestrator() -> ContentProcessorOrchestrator:
    config_service = get_config_service()
    provider_config = build_provider_config(config_service, "content_processor")
    return ContentProcessorOrchestrator(
        content_repository=get_content_repository(),
        llm_provider=provider_config.create_provider(),
        model=provider_config.model,
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
        tracer.shutdown()
        logger.flush()
        health_task.cancel()
        asyncio.create_task(consumer.close())

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    await consumer.start()


if __name__ == "__main__":
    asyncio.run(main())
