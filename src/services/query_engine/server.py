"""Query Engine Service - consumes query messages and produces answers."""
import asyncio
import signal

from src.services.query_engine.query_engine_orchestrator import QueryEngineOrchestrator
from src.utils.observability.logs.logger import Logger
from src.utils.queue.messaging_factory import get_message_consumer
from src.utils.queue.queue_message_handler import ThreadPoolMessageDispatcher
from src.utils.services.aws.appconfig_service import get_config_service
from src.utils.services.clients.mongodb_client import get_content_repository
from src.utils.services.clients.redis_client import get_state_repository
from src.utils.services.config.health import start_health_server_background
from src.utils.services.config.ports import get_service_port
from src.utils.services.inference.provider_config_builder import build_provider_config

logger = Logger()

SERVICE_PORT_KEY = "services.query_engine.port"
DEFAULT_PORT = 8004


def create_query_engine_orchestrator() -> QueryEngineOrchestrator:
    config_service = get_config_service()
    provider_config = build_provider_config(config_service, "query_engine")
    return QueryEngineOrchestrator(
        state_repository=get_state_repository(),
        content_repository=get_content_repository(),
        llm_provider=provider_config.create_provider(),
        model=provider_config.model,
    )


async def main():
    logger.info("Starting Query Engine Service")

    orchestrator = create_query_engine_orchestrator()
    handler = ThreadPoolMessageDispatcher(orchestrator)
    consumer = get_message_consumer(handler, service_name="query_engine")

    port = get_service_port(SERVICE_PORT_KEY, default=DEFAULT_PORT)
    logger.info(f"Starting health server on port {port}")
    health_task = start_health_server_background(
        service_name="Query Engine Service",
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
