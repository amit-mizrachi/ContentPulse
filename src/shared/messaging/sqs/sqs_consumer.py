import asyncio

from src.shared.interfaces.message_consumer import AsyncMessageConsumer
from src.shared.observability.logs.logger import Logger
from src.shared.interfaces.message_dispatcher import MessageDispatcher
from src.shared.messaging.sqs.sqs_message_processor import SQSMessageProcessor
from src.shared.messaging.sqs.sqs_poller import SQSPoller
from src.shared.messaging.sqs.sqs_visibility_extender import SQSVisibilityExtender


class SQSConsumer(AsyncMessageConsumer):
    def __init__(self, message_handler: MessageDispatcher, queue_config_key: str = "sqs.queue_url"):
        self.__logger = Logger()

        self.__visibility_extender = SQSVisibilityExtender(queue_config_key)
        self.__poller = SQSPoller(queue_config_key)
        self.__processor = SQSMessageProcessor(
            self.__visibility_extender,
            message_handler,
            queue_config_key
        )

        self.closed = False

    async def start(self) -> None:
        event_loop = asyncio.get_running_loop()
        self.__processor.set_event_loop(event_loop)

        self.__logger.info("Starting visibility extension loop")
        self.__visibility_extender.start()

        try:
            await self.__poll_loop()
        finally:
            await self.close()
            self.__logger.warning("SQSConsumer poll loop ended")

    async def __poll_loop(self):
        self.__logger.info("Starting message polling loop")
        async for parsed_messages in self.__poller.poll_for_messages():
            if self.closed:
                break

            for parsed_message in parsed_messages:
                if self.closed:
                    break

                self.__logger.debug("SQS message received")
                await self.__processor.acquire_slot()
                try:
                    await self.__processor.process_message(parsed_message)
                except Exception as e:
                    self.__logger.error(f"Unhandled error in message processing: {parsed_message.get('message_id')}")

    async def close(self) -> None:
        self.closed = True
        self.__poller.close()
        self.__visibility_extender.close()
        self.__processor.close()


def get_sqs_consumer(handler: MessageDispatcher, queue_config_key: str = "sqs.queue_url") -> SQSConsumer:
    return SQSConsumer(handler, queue_config_key)
