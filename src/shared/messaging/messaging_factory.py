"""Config-driven broker selection for message publishing and consuming."""
from functools import lru_cache

from src.shared.interfaces.messaging.message_consumer import AsyncMessageConsumer
from src.shared.interfaces.messaging.message_publisher import MessagePublisher
from src.shared.interfaces.messaging.message_dispatcher import MessageDispatcher
from src.shared.appconfig_client import get_config_service

CONSUMER_CONFIG_KEYS = {
    "sns_sqs": {
        "content_processor": "sqs.content_processor_queue_url",
        "query_engine": "sqs.query_engine_queue_url",
    },
    "kafka": {
        "content_processor": "kafka.content_raw_topic",
        "query_engine": "kafka.query_topic",
    },
}


@lru_cache(maxsize=1)
def get_message_publisher() -> MessagePublisher:
    config = get_config_service()
    broker = config.get("messaging.broker", "sns_sqs")

    if broker == "kafka":
        from src.shared.messaging.kafka import get_kafka_publisher
        return get_kafka_publisher()
    else:
        from src.shared.messaging.sqs.sns_message_publisher import get_sns_service
        return get_sns_service()


def get_message_consumer(handler: MessageDispatcher, service_name: str) -> AsyncMessageConsumer:
    config = get_config_service()
    broker = config.get("messaging.broker", "sns_sqs")
    config_key = CONSUMER_CONFIG_KEYS[broker][service_name]

    if broker == "kafka":
        from src.shared.messaging.kafka import get_kafka_consumer
        return get_kafka_consumer(handler, topic_config_key=config_key)
    else:
        from src.shared.messaging.sqs import get_sqs_consumer
        return get_sqs_consumer(handler, queue_config_key=config_key)
