"""Unit tests for KafkaConsumer."""
import asyncio
import json
import pytest
from unittest.mock import MagicMock, patch, AsyncMock


class TestKafkaConsumer:
    """Tests for KafkaConsumer message consuming."""

    @patch('src.utils.queue.kafka.kafka_consumer.Consumer')
    @patch('src.utils.queue.kafka.kafka_consumer.Logger')
    @patch('src.utils.queue.kafka.kafka_consumer.get_config_service')
    def test_implements_async_message_consumer(self, mock_get_config, mock_logger, mock_consumer_cls):
        """KafkaConsumer should implement AsyncMessageConsumer interface."""
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            "kafka.bootstrap_servers": "localhost:9092",
            "kafka.group_id": "test-group",
            "kafka.auto_offset_reset": "earliest",
            "kafka.inference_topic": "test-inference",
        }.get(key, default)
        mock_get_config.return_value = mock_config

        mock_handler = MagicMock()

        from src.utils.queue.kafka.kafka_consumer import KafkaConsumer
        from src.interfaces.message_consumer import AsyncMessageConsumer

        consumer = KafkaConsumer(mock_handler, topic_config_key="kafka.inference_topic")
        assert isinstance(consumer, AsyncMessageConsumer)

    @patch('src.utils.queue.kafka.kafka_consumer.Consumer')
    @patch('src.utils.queue.kafka.kafka_consumer.Logger')
    @patch('src.utils.queue.kafka.kafka_consumer.get_config_service')
    def test_subscribes_to_configured_topic(self, mock_get_config, mock_logger, mock_consumer_cls):
        """KafkaConsumer should subscribe to the topic from config."""
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            "kafka.bootstrap_servers": "localhost:9092",
            "kafka.group_id": "test-group",
            "kafka.auto_offset_reset": "earliest",
            "kafka.inference_topic": "my-inference-topic",
        }.get(key, default)
        mock_get_config.return_value = mock_config

        mock_consumer = MagicMock()
        mock_consumer_cls.return_value = mock_consumer

        mock_handler = MagicMock()

        from src.utils.queue.kafka.kafka_consumer import KafkaConsumer

        KafkaConsumer(mock_handler, topic_config_key="kafka.inference_topic")

        mock_consumer.subscribe.assert_called_once_with(["my-inference-topic"])

    @pytest.mark.asyncio
    @patch('src.utils.queue.kafka.kafka_consumer.Consumer')
    @patch('src.utils.queue.kafka.kafka_consumer.Logger')
    @patch('src.utils.queue.kafka.kafka_consumer.get_config_service')
    async def test_close_stops_consumer(self, mock_get_config, mock_logger, mock_consumer_cls):
        """close() should stop the consumer loop and close the Kafka consumer."""
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            "kafka.bootstrap_servers": "localhost:9092",
            "kafka.group_id": "test-group",
            "kafka.auto_offset_reset": "earliest",
            "kafka.inference_topic": "test-inference",
        }.get(key, default)
        mock_get_config.return_value = mock_config

        mock_consumer = MagicMock()
        mock_consumer_cls.return_value = mock_consumer

        mock_handler = MagicMock()

        from src.utils.queue.kafka.kafka_consumer import KafkaConsumer

        consumer = KafkaConsumer(mock_handler, topic_config_key="kafka.inference_topic")

        await consumer.close()

        assert consumer._closed is True
        mock_consumer.close.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.utils.queue.kafka.kafka_consumer.Consumer')
    @patch('src.utils.queue.kafka.kafka_consumer.Logger')
    @patch('src.utils.queue.kafka.kafka_consumer.get_config_service')
    async def test_commits_offset_on_success(self, mock_get_config, mock_logger, mock_consumer_cls):
        """Should commit offset when handler returns True."""
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            "kafka.bootstrap_servers": "localhost:9092",
            "kafka.group_id": "test-group",
            "kafka.auto_offset_reset": "earliest",
            "kafka.inference_topic": "test-inference",
        }.get(key, default)
        mock_get_config.return_value = mock_config

        mock_consumer = MagicMock()
        mock_consumer_cls.return_value = mock_consumer

        # Create a mock message
        mock_msg = MagicMock()
        mock_msg.error.return_value = None
        mock_msg.value.return_value = json.dumps({"request_id": "test-123"}).encode("utf-8")

        # First poll returns a message, second poll triggers close
        call_count = 0

        def poll_side_effect(timeout):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_msg
            return None

        mock_consumer.poll = poll_side_effect

        # Handler returns True (success)
        from concurrent.futures import Future
        mock_handler = MagicMock()
        future = Future()
        future.set_result(True)
        mock_handler.submit.return_value = future

        from src.utils.queue.kafka.kafka_consumer import KafkaConsumer

        consumer = KafkaConsumer(mock_handler, topic_config_key="kafka.inference_topic")

        # Run consumer briefly then close
        async def run_then_close():
            await asyncio.sleep(0.3)
            await consumer.close()

        await asyncio.gather(consumer.start(), run_then_close())

        mock_consumer.commit.assert_called_once_with(message=mock_msg)

    @pytest.mark.asyncio
    @patch('src.utils.queue.kafka.kafka_consumer.Consumer')
    @patch('src.utils.queue.kafka.kafka_consumer.Logger')
    @patch('src.utils.queue.kafka.kafka_consumer.get_config_service')
    async def test_does_not_commit_on_handler_failure(self, mock_get_config, mock_logger, mock_consumer_cls):
        """Should NOT commit offset when handler returns False."""
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: {
            "kafka.bootstrap_servers": "localhost:9092",
            "kafka.group_id": "test-group",
            "kafka.auto_offset_reset": "earliest",
            "kafka.inference_topic": "test-inference",
        }.get(key, default)
        mock_get_config.return_value = mock_config

        mock_consumer = MagicMock()
        mock_consumer_cls.return_value = mock_consumer

        mock_msg = MagicMock()
        mock_msg.error.return_value = None
        mock_msg.value.return_value = json.dumps({"request_id": "test-123"}).encode("utf-8")

        call_count = 0

        def poll_side_effect(timeout):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_msg
            return None

        mock_consumer.poll = poll_side_effect

        from concurrent.futures import Future
        mock_handler = MagicMock()
        future = Future()
        future.set_result(False)
        mock_handler.submit.return_value = future

        from src.utils.queue.kafka.kafka_consumer import KafkaConsumer

        consumer = KafkaConsumer(mock_handler, topic_config_key="kafka.inference_topic")

        async def run_then_close():
            await asyncio.sleep(0.3)
            await consumer.close()

        await asyncio.gather(consumer.start(), run_then_close())

        mock_consumer.commit.assert_not_called()
