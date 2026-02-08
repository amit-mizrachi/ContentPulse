import asyncio
import signal

from src.services.inference.inference_orchestrator import InferenceOrchestrator
from src.utils.observability.logs.logger import Logger
from src.utils.queue.messaging_factory import get_message_consumer, get_message_publisher
from src.utils.queue.queue_message_handler import QueueMessageHandler
from src.utils.services.aws.appconfig_service import get_config_service
from src.utils.services.clients.redis_client import get_state_repository
from src.utils.services.config.health import start_health_server_background
from src.utils.services.config.ports import get_service_port
from src.utils.services.llm.llm_provider_factory import DefaultLLMProviderFactory

logger = Logger()

SERVICE_PORT_KEY = "services.inference.port"
DEFAULT_PORT = 8003


def create_inference_orchestrator() -> InferenceOrchestrator:
    config_service = get_config_service()
    return InferenceOrchestrator(
        state_repository=get_state_repository(),
        message_publisher=get_message_publisher(),
        llm_factory=DefaultLLMProviderFactory(),
        judge_topic=config_service.get("topics.judge", "judge"),
    )


async def main():
    logger.info("Starting Inference Service")

    orchestrator = create_inference_orchestrator()
    handler = QueueMessageHandler(orchestrator)
    consumer = get_message_consumer(handler, service_name="inference")

    port = get_service_port(SERVICE_PORT_KEY, default=DEFAULT_PORT)
    logger.info(f"Starting health server on port {port}")
    health_task = start_health_server_background(
        service_name="Inference Service",
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
