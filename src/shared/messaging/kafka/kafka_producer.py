"""Kafka message publisher using confluent-kafka."""
from functools import lru_cache

from confluent_kafka import Producer

from src.shared.interfaces.messaging.message_publisher import MessagePublisher
from src.shared.observability.logs.logger import Logger
from src.shared.observability.traces.spans.span_context_factory import SpanContextFactory
from src.shared.appconfig_client import get_config_service


class KafkaPublisher(MessagePublisher):
    def __init__(self):
        self._appconfig = get_config_service()
        self._logger = Logger()

        self._producer = Producer({
            "bootstrap.servers": self._appconfig.get("kafka.bootstrap_servers"),
            "client.id": self._appconfig.get("kafka.client_id", "simple-sport-news-producer"),
        })

        self._topic_map = {
            "content-raw": self._appconfig.get("kafka.content_raw_topic"),
            "query": self._appconfig.get("kafka.query_topic"),
        }

    def publish(self, topic_name: str, message: str) -> bool:
        kafka_topic = self._topic_map.get(topic_name, topic_name)
        try:
            with SpanContextFactory.client("KAFKA", self._producer, "kafka_producer", "produce"):
                self._producer.produce(kafka_topic, value=message.encode("utf-8"))
                remaining = self._producer.flush(timeout=10)
                if remaining > 0:
                    raise Exception(f"Kafka flush timed out with {remaining} messages pending")

            self._logger.info(f"Published message to Kafka topic {kafka_topic}")
            return True
        except Exception as e:
            self._logger.error(f"Failed to publish message to Kafka topic {kafka_topic}: {e}")
            raise


@lru_cache(maxsize=1)
def get_kafka_publisher() -> KafkaPublisher:
    return KafkaPublisher()
