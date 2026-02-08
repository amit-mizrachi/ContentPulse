import asyncio
import signal

from src.services.judge.judge_orchestrator import JudgeOrchestrator
from src.utils.observability.logs.logger import Logger
from src.utils.queue.messaging_factory import get_message_consumer
from src.utils.queue.queue_message_handler import QueueMessageHandler
from src.utils.services.clients.redis_client import get_state_repository
from src.utils.services.clients.persistence_client import get_persistence_gateway
from src.utils.services.clients.judge_inference_client import get_judge_gateway
from src.utils.services.config.health import start_health_server_background
from src.utils.services.config.ports import get_service_port

logger = Logger()

SERVICE_PORT_KEY = "services.judge.port"
DEFAULT_PORT = 8004


def create_judge_orchestrator() -> JudgeOrchestrator:
    return JudgeOrchestrator(
        state_repository=get_state_repository(),
        persistence_gateway=get_persistence_gateway(),
        judge_gateway=get_judge_gateway(),
    )


async def main():
    logger.info("Starting Judge Service")

    orchestrator = create_judge_orchestrator()
    handler = QueueMessageHandler(orchestrator)
    consumer = get_message_consumer(handler, service_name="judge")

    port = get_service_port(SERVICE_PORT_KEY, default=DEFAULT_PORT)
    logger.info(f"Starting health server on port {port}")
    health_task = start_health_server_background(
        service_name="Judge Service",
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
