import asyncio
from datetime import datetime, timezone

from src.shared.appconfig_client import get_config_service
from src.shared.messaging.sqs.sqs_client import get_sqs_service
from src.shared.observability.logs.logger import Logger
from src.shared.messaging.sqs.sqs_message_parser import SQSMessageParser


class SQSPoller:
    def __init__(self, queue_config_key: str = "sqs.queue_url"):
        self.__appconfig = get_config_service()
        self.__logger = Logger()
        self.__sqs_service = get_sqs_service()

        self.__message_parser = SQSMessageParser()
        self.__queue_url = self.__appconfig.get(queue_config_key)
        self.__seconds_between_receive_attempts = self.__appconfig.get(
            "sqs.seconds_between_receive_attempts", 1
        )

        self.__last_receive_attempt: datetime = datetime.now(timezone.utc)
        self.__messages_received_in_last_attempt: int = 0
        self.__closed: bool = False

    async def poll_for_messages(self):
        while not self.__closed:
            try:
                received_messages = self.__sqs_service.receive_message(self.__queue_url)

                if received_messages is not None:
                    parsed_messages = self.__message_parser.parse_messages(received_messages)
                    self.__messages_received_in_last_attempt = len(parsed_messages)
                    yield parsed_messages
                else:
                    self.__messages_received_in_last_attempt = 0
                    self.__logger.warning("Could not handle message from queue")
                    yield []

                await self.__sleep_between_receive_attempts()

            except Exception as e:
                self.__logger.error(f"Could not poll messages from queue: {e}")
                yield []

    async def __sleep_between_receive_attempts(self):
        if self.__messages_received_in_last_attempt == 0:
            datetime_now = datetime.now(timezone.utc)
            time_delta = datetime_now - self.__last_receive_attempt
            seconds_left_to_sleep = self.__seconds_between_receive_attempts - time_delta.total_seconds()

            actual_sleep = max(seconds_left_to_sleep, 1e-3)
            await asyncio.sleep(actual_sleep)

            self.__last_receive_attempt = datetime.now(timezone.utc)

    def close(self):
        self.__closed = True

    @property
    def closed(self):
        return self.__closed
