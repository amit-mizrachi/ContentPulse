"""Config-driven broker selection for message publishing and consuming."""
from functools import lru_cache

from src.interfaces.message_consumer import AsyncMessageConsumer
from src.interfaces.message_publisher import MessagePublisher
from src.utils.queue.queue_message_handler import QueueMessageHandler
from src.utils.services.aws.appconfig_service import get_config_service

CONSUMER_CONFIG_KEYS = {
    "sns_sqs": {
        "inference": "sqs.inference_queue_url",
        "judge": "sqs.judge_queue_url",
    },
    "kafka": {
        "inference": "kafka.inference_topic",
        "judge": "kafka.judge_topic",
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


def get_message_consumer(handler: QueueMessageHandler, service_name: str) -> AsyncMessageConsumer:
    config = get_config_service()
    broker = config.get("messaging.broker", "sns_sqs")
    config_key = CONSUMER_CONFIG_KEYS[broker][service_name]

    if broker == "kafka":
        from src.utils.queue.kafka import get_kafka_consumer
        return get_kafka_consumer(handler, topic_config_key=config_key)

    from src.utils.queue.sqs import get_sqs_consumer
    return get_sqs_consumer(handler, queue_config_key=config_key)
