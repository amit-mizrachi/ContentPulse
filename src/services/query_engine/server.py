"""Query Engine Service - consumes query messages and produces answers."""
import asyncio
import signal

from src.services.query_engine.query_engine_orchestrator import QueryEngineOrchestrator
from src.shared.observability.logs.logger import Logger
from src.shared.observability.traces.tracer import Tracer
from src.shared.messaging.messaging_factory import get_message_consumer
from src.shared.messaging.thread_pool_message_dispatcher import ThreadPoolMessageDispatcher
from src.shared.appconfig_client import get_config_service
from src.shared.repositories.mongodb_article_repository import get_content_repository
from src.shared.repositories.redis_state_repository import get_state_repository
from src.shared.health import start_health_server_background
from src.shared.inference.provider_config_builder import build_provider_config

logger = Logger()
tracer = Tracer()


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

    port = int(get_config_service().get("services.query_engine.port"))
    logger.info(f"Starting health server on port {port}")
    health_task = start_health_server_background(
        service_name="Query Engine Service",
        port=port
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
