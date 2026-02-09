"""Kafka message consumer using confluent-kafka with async wrapper."""
import asyncio
import json

from confluent_kafka import Consumer, KafkaError

from src.shared.interfaces.messaging.message_consumer import AsyncMessageConsumer
from src.shared.observability.logs.logger import Logger
from src.shared.interfaces.messaging.message_dispatcher import MessageDispatcher
from src.shared.observability.traces.spans.span_context_factory import SpanContextFactory
from src.shared.observability.traces.spans.spanner import Spanner
from src.shared.aws.appconfig_service import get_config_service


class KafkaConsumer(AsyncMessageConsumer):
    def __init__(self, message_handler: MessageDispatcher, topic_config_key: str):
        self._appconfig = get_config_service()
        self._logger = Logger()
        self._handler = message_handler
        self._spanner = Spanner()
        self._closed = False

        kafka_topic = self._appconfig.get(topic_config_key)
        self._topic = kafka_topic

        self._consumer = Consumer({
            "bootstrap.servers": self._appconfig.get("kafka.bootstrap_servers"),
            "group.id": self._appconfig.get("kafka.group_id", "simple-sport-news"),
            "auto.offset.reset": self._appconfig.get("kafka.auto_offset_reset", "earliest"),
            "enable.auto.commit": False,
        })
        self._consumer.subscribe([self._topic])

    async def start(self) -> None:
        self._logger.info(f"Starting Kafka consumer for topic {self._topic}")
        loop = asyncio.get_running_loop()

        while not self._closed:
            try:
                msg = await loop.run_in_executor(None, self._consumer.poll, 1.0)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    self._logger.error(f"Kafka consumer error: {msg.error()}")
                    continue

                await self._process_message(msg)

            except Exception as e:
                if not self._closed:
                    self._logger.error(f"Error in Kafka consumer loop: {e}")

    async def _process_message(self, msg) -> None:
        try:
            message_contents = json.loads(msg.value().decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            self._logger.error(f"Failed to parse Kafka message: {e}")
            self._consumer.commit(message=msg)
            return

        telemetry_headers = message_contents.get("telemetry_headers", {})
        telemetry_context = self._spanner.extract_telemetry_context(telemetry_headers)
        message_id = message_contents.get("request_id", "")

        try:
            with SpanContextFactory.consumer(self._topic, message_id, message_contents, messaging_system="KAFKA", telemetry_context=telemetry_context):
                result_future = self._handler.submit(message_contents)

                loop = asyncio.get_running_loop()
                success = await loop.run_in_executor(None, result_future.result)

                if success:
                    self._consumer.commit(message=msg)
                else:
                    self._logger.warning(f"Handler returned failure for message on {self._topic}")
        except Exception as e:
            self._logger.error(f"Error processing Kafka message: {e}")

    async def close(self) -> None:
        self._closed = True
        self._consumer.close()
        self._logger.info(f"Kafka consumer for topic {self._topic} closed")


def get_kafka_consumer(handler: MessageDispatcher, topic_config_key: str) -> KafkaConsumer:
    """Create a KafkaConsumer instance."""
    return KafkaConsumer(handler, topic_config_key)
