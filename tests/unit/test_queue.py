"""Tests for messaging factory configuration."""
from src.utils.queue.messaging_factory import CONSUMER_CONFIG_KEYS


class TestMessagingFactory:
    def test_consumer_config_has_content_processor(self):
        assert "content_processor" in CONSUMER_CONFIG_KEYS["kafka"]
        assert "content_processor" in CONSUMER_CONFIG_KEYS["sns_sqs"]

    def test_consumer_config_has_query_engine(self):
        assert "query_engine" in CONSUMER_CONFIG_KEYS["kafka"]
        assert "query_engine" in CONSUMER_CONFIG_KEYS["sns_sqs"]

    def test_no_old_service_names(self):
        for broker in CONSUMER_CONFIG_KEYS:
            assert "inference" not in CONSUMER_CONFIG_KEYS[broker]
            assert "judge" not in CONSUMER_CONFIG_KEYS[broker]

    def test_kafka_topics(self):
        assert CONSUMER_CONFIG_KEYS["kafka"]["content_processor"] == "kafka.content_raw_topic"
        assert CONSUMER_CONFIG_KEYS["kafka"]["query_engine"] == "kafka.query_topic"
