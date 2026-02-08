"""Unit tests for messaging_factory module."""
from unittest.mock import MagicMock, patch


class TestGetMessagePublisher:
    """Tests for get_message_publisher factory function."""

    def setup_method(self):
        from src.utils.queue.messaging_factory import get_message_publisher
        get_message_publisher.cache_clear()

    def teardown_method(self):
        from src.utils.queue.messaging_factory import get_message_publisher
        get_message_publisher.cache_clear()

    @patch('src.utils.services.aws.sns_service.SNSService')
    @patch('src.utils.services.aws.sns_service.get_sns_service')
    @patch('src.utils.queue.messaging_factory.get_config_service')
    def test_returns_sns_service_by_default(self, mock_get_config, mock_get_sns, mock_sns_cls):
        """Default broker should return SNS publisher."""
        mock_config = MagicMock()
        mock_config.get.return_value = "sns_sqs"
        mock_get_config.return_value = mock_config

        mock_sns = MagicMock()
        mock_get_sns.return_value = mock_sns

        from src.utils.queue.messaging_factory import get_message_publisher
        result = get_message_publisher()

        assert result is mock_sns

    @patch('src.utils.queue.kafka.kafka_producer.KafkaPublisher')
    @patch('src.utils.queue.messaging_factory.get_config_service')
    def test_returns_kafka_publisher_when_configured(self, mock_get_config, mock_kafka_cls):
        """Kafka broker should return Kafka publisher."""
        mock_config = MagicMock()
        mock_config.get.return_value = "kafka"
        mock_get_config.return_value = mock_config

        mock_kafka_instance = MagicMock()
        mock_kafka_cls.return_value = mock_kafka_instance

        from src.utils.queue.messaging_factory import get_message_publisher
        from src.utils.queue.kafka.kafka_producer import get_kafka_publisher
        get_kafka_publisher.cache_clear()

        result = get_message_publisher()

        assert result is mock_kafka_instance

        get_kafka_publisher.cache_clear()


class TestGetMessageConsumer:
    """Tests for get_message_consumer factory function."""

    @patch('src.utils.queue.sqs.sqs_consumer.SQSConsumer')
    @patch('src.utils.queue.messaging_factory.get_config_service')
    def test_returns_sqs_consumer_for_inference(self, mock_get_config, mock_sqs_cls):
        """SNS/SQS broker should return SQS consumer with correct queue key."""
        mock_config = MagicMock()
        mock_config.get.return_value = "sns_sqs"
        mock_get_config.return_value = mock_config

        mock_consumer = MagicMock()
        mock_sqs_cls.return_value = mock_consumer

        mock_handler = MagicMock()

        from src.utils.queue.messaging_factory import get_message_consumer

        result = get_message_consumer(mock_handler, service_name="inference")

        assert result is mock_consumer
        mock_sqs_cls.assert_called_once_with(mock_handler, "sqs.inference_queue_url")

    @patch('src.utils.queue.sqs.sqs_consumer.SQSConsumer')
    @patch('src.utils.queue.messaging_factory.get_config_service')
    def test_returns_sqs_consumer_for_judge(self, mock_get_config, mock_sqs_cls):
        """SNS/SQS broker should use judge queue URL for judge service."""
        mock_config = MagicMock()
        mock_config.get.return_value = "sns_sqs"
        mock_get_config.return_value = mock_config

        mock_consumer = MagicMock()
        mock_sqs_cls.return_value = mock_consumer

        mock_handler = MagicMock()

        from src.utils.queue.messaging_factory import get_message_consumer

        result = get_message_consumer(mock_handler, service_name="judge")

        mock_sqs_cls.assert_called_once_with(mock_handler, "sqs.judge_queue_url")

    @patch('src.utils.queue.kafka.kafka_consumer.KafkaConsumer')
    @patch('src.utils.queue.messaging_factory.get_config_service')
    def test_returns_kafka_consumer_for_inference(self, mock_get_config, mock_kafka_cls):
        """Kafka broker should return Kafka consumer with correct topic key."""
        mock_config = MagicMock()
        mock_config.get.return_value = "kafka"
        mock_get_config.return_value = mock_config

        mock_consumer = MagicMock()
        mock_kafka_cls.return_value = mock_consumer

        mock_handler = MagicMock()

        from src.utils.queue.messaging_factory import get_message_consumer

        result = get_message_consumer(mock_handler, service_name="inference")

        assert result is mock_consumer
        mock_kafka_cls.assert_called_once_with(mock_handler, "kafka.inference_topic")

    @patch('src.utils.queue.kafka.kafka_consumer.KafkaConsumer')
    @patch('src.utils.queue.messaging_factory.get_config_service')
    def test_returns_kafka_consumer_for_judge(self, mock_get_config, mock_kafka_cls):
        """Kafka broker should use judge topic key for judge service."""
        mock_config = MagicMock()
        mock_config.get.return_value = "kafka"
        mock_get_config.return_value = mock_config

        mock_consumer = MagicMock()
        mock_kafka_cls.return_value = mock_consumer

        mock_handler = MagicMock()

        from src.utils.queue.messaging_factory import get_message_consumer

        result = get_message_consumer(mock_handler, service_name="judge")

        mock_kafka_cls.assert_called_once_with(mock_handler, "kafka.judge_topic")
