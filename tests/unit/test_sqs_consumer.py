"""Unit tests for SQS consumer abstraction."""
from unittest.mock import patch, MagicMock

from src.interfaces.message_consumer import AsyncMessageConsumer
from src.utils.queue.sqs.sqs_consumer import SQSConsumer, get_sqs_consumer


class TestSQSConsumerInterface:
    @patch('src.utils.queue.sqs.sqs_consumer.SQSVisibilityExtender')
    @patch('src.utils.queue.sqs.sqs_consumer.SQSPoller')
    @patch('src.utils.queue.sqs.sqs_consumer.SQSMessageProcessor')
    @patch('src.utils.queue.sqs.sqs_consumer.Logger')
    def test_sqs_consumer_is_message_consumer(self, mock_logger, mock_processor, mock_poller, mock_extender):
        handler = MagicMock()
        handler.max_worker_count = 2

        consumer = SQSConsumer(handler, queue_config_key="sqs.test_queue_url")

        assert isinstance(consumer, AsyncMessageConsumer)

    @patch('src.utils.queue.sqs.sqs_consumer.SQSVisibilityExtender')
    @patch('src.utils.queue.sqs.sqs_consumer.SQSPoller')
    @patch('src.utils.queue.sqs.sqs_consumer.SQSMessageProcessor')
    @patch('src.utils.queue.sqs.sqs_consumer.Logger')
    def test_get_sqs_consumer_returns_message_consumer(self, mock_logger, mock_processor, mock_poller, mock_extender):
        handler = MagicMock()
        handler.max_worker_count = 2

        consumer = get_sqs_consumer(handler, queue_config_key="sqs.test_queue_url")

        assert isinstance(consumer, AsyncMessageConsumer)
        assert isinstance(consumer, SQSConsumer)
