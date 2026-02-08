"""Config-driven broker selection for message publishing and consuming."""
from functools import lru_cache

from src.interfaces.message_consumer import AsyncMessageConsumer
from src.interfaces.message_publisher import MessagePublisher
from src.interfaces.message_dispatcher import MessageDispatcher
from src.utils.services.aws.appconfig_service import get_config_service

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
        from src.utils.queue.kafka import get_kafka_publisher
        return get_kafka_publisher()

    from src.utils.services.aws.sns_service import get_sns_service
    return get_sns_service()


def get_message_consumer(handler: MessageDispatcher, service_name: str) -> AsyncMessageConsumer:
    config = get_config_service()
    broker = config.get("messaging.broker", "sns_sqs")
    config_key = CONSUMER_CONFIG_KEYS[broker][service_name]

    if broker == "kafka":
        from src.utils.queue.kafka import get_kafka_consumer
        return get_kafka_consumer(handler, topic_config_key=config_key)

    from src.utils.queue.sqs import get_sqs_consumer
    return get_sqs_consumer(handler, queue_config_key=config_key)
