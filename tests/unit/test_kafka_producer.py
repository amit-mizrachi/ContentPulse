"""Unit tests for KafkaPublisher."""
import pytest
from unittest.mock import MagicMock, patch


class TestKafkaPublisher:
    """Tests for KafkaPublisher message publishing."""

    @patch('src.utils.queue.kafka.kafka_producer.Producer')
    @patch('src.utils.queue.kafka.kafka_producer.Logger')
    @patch('src.utils.queue.kafka.kafka_producer.get_config_service')
    def test_implements_message_publisher(self, mock_get_config, mock_logger, mock_producer_cls):
        """KafkaPublisher should implement MessagePublisher interface."""
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            "kafka.bootstrap_servers": "localhost:9092",
            "kafka.client_id": "test-producer",
            "kafka.inference_topic": "test-inference",
            "kafka.judge_topic": "test-judge",
        }.get(key, default)
        mock_get_config.return_value = mock_config

        from src.utils.queue.kafka.kafka_producer import KafkaPublisher
        from src.interfaces.message_publisher import MessagePublisher

        publisher = KafkaPublisher()
        assert isinstance(publisher, MessagePublisher)

    @patch('src.utils.queue.kafka.kafka_producer.Producer')
    @patch('src.utils.queue.kafka.kafka_producer.Logger')
    @patch('src.utils.queue.kafka.kafka_producer.get_config_service')
    def test_publish_calls_produce_and_flush(self, mock_get_config, mock_logger, mock_producer_cls):
        """publish() should call producer.produce() and flush()."""
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            "kafka.bootstrap_servers": "localhost:9092",
            "kafka.client_id": "test-producer",
            "kafka.inference_topic": "test-inference",
            "kafka.judge_topic": "test-judge",
        }.get(key, default)
        mock_get_config.return_value = mock_config

        mock_producer = MagicMock()
        mock_producer.flush.return_value = 0
        mock_producer_cls.return_value = mock_producer

        from src.utils.queue.kafka.kafka_producer import KafkaPublisher

        publisher = KafkaPublisher()
        result = publisher.publish("inference", '{"request_id": "test-123"}')

        assert result is True
        mock_producer.produce.assert_called_once_with(
            "test-inference",
            value=b'{"request_id": "test-123"}'
        )
        mock_producer.flush.assert_called_once_with(timeout=10)

    @patch('src.utils.queue.kafka.kafka_producer.Producer')
    @patch('src.utils.queue.kafka.kafka_producer.Logger')
    @patch('src.utils.queue.kafka.kafka_producer.get_config_service')
    def test_publish_resolves_topic_name(self, mock_get_config, mock_logger, mock_producer_cls):
        """publish() should resolve logical topic name to Kafka topic."""
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            "kafka.bootstrap_servers": "localhost:9092",
            "kafka.client_id": "test-producer",
            "kafka.inference_topic": "my-custom-inference-topic",
            "kafka.judge_topic": "my-custom-judge-topic",
        }.get(key, default)
        mock_get_config.return_value = mock_config

        mock_producer = MagicMock()
        mock_producer.flush.return_value = 0
        mock_producer_cls.return_value = mock_producer

        from src.utils.queue.kafka.kafka_producer import KafkaPublisher

        publisher = KafkaPublisher()
        publisher.publish("judge", '{"data": "test"}')

        mock_producer.produce.assert_called_once_with(
            "my-custom-judge-topic",
            value=b'{"data": "test"}'
        )

    @patch('src.utils.queue.kafka.kafka_producer.Producer')
    @patch('src.utils.queue.kafka.kafka_producer.Logger')
    @patch('src.utils.queue.kafka.kafka_producer.get_config_service')
    def test_publish_raises_on_flush_timeout(self, mock_get_config, mock_logger, mock_producer_cls):
        """publish() should raise when flush times out with pending messages."""
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            "kafka.bootstrap_servers": "localhost:9092",
            "kafka.client_id": "test-producer",
            "kafka.inference_topic": "test-inference",
            "kafka.judge_topic": "test-judge",
        }.get(key, default)
        mock_get_config.return_value = mock_config

        mock_producer = MagicMock()
        mock_producer.flush.return_value = 1  # 1 message still pending
        mock_producer_cls.return_value = mock_producer

        from src.utils.queue.kafka.kafka_producer import KafkaPublisher

        publisher = KafkaPublisher()

        with pytest.raises(Exception, match="flush timed out"):
            publisher.publish("inference", '{"data": "test"}')

    @patch('src.utils.queue.kafka.kafka_producer.Producer')
    @patch('src.utils.queue.kafka.kafka_producer.Logger')
    @patch('src.utils.queue.kafka.kafka_producer.get_config_service')
    def test_publish_raises_on_produce_error(self, mock_get_config, mock_logger, mock_producer_cls):
        """publish() should propagate produce errors."""
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            "kafka.bootstrap_servers": "localhost:9092",
            "kafka.client_id": "test-producer",
            "kafka.inference_topic": "test-inference",
            "kafka.judge_topic": "test-judge",
        }.get(key, default)
        mock_get_config.return_value = mock_config

        mock_producer = MagicMock()
        mock_producer.produce.side_effect = Exception("Buffer full")
        mock_producer_cls.return_value = mock_producer

        from src.utils.queue.kafka.kafka_producer import KafkaPublisher

        publisher = KafkaPublisher()

        with pytest.raises(Exception, match="Buffer full"):
            publisher.publish("inference", '{"data": "test"}')
