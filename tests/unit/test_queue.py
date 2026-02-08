"""Unit tests for queue module."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from concurrent.futures import Future
from datetime import datetime, timezone

from src.utils.queue.context_preserving_executor import ContextPreservingExecutor
from src.utils.queue.sqs.sqs_message_parser import SQSMessageParser
from src.utils.queue.queue_message_handler import QueueMessageHandler
from src.interfaces.message_handler import MessageHandler


class TestContextPreservingExecutor:
    def test_executor_inherits_from_thread_pool(self):
        executor = ContextPreservingExecutor(max_workers=2)
        assert hasattr(executor, 'submit')
        executor.shutdown(wait=False)

    def test_executor_runs_callable(self):
        executor = ContextPreservingExecutor(max_workers=2)
        result = []

        def task():
            result.append(42)
            return True

        future = executor.submit(task)
        future.result(timeout=5)

        assert result == [42]
        executor.shutdown(wait=True)

    def test_executor_passes_arguments(self):
        executor = ContextPreservingExecutor(max_workers=2)

        def add(a, b):
            return a + b

        future = executor.submit(add, 2, 3)
        assert future.result(timeout=5) == 5
        executor.shutdown(wait=True)


class TestQueueMessageParser:
    @patch('src.utils.queue.sqs.sqs_message_parser.Logger')
    def test_parse_valid_sns_message(self, mock_logger):
        parser = SQSMessageParser()

        messages = [{
            "MessageId": "msg-123",
            "ReceiptHandle": "handle-123",
            "Body": '{"Message": "{\\"key\\": \\"value\\"}", "MessageAttributes": {"attr1": {"Type": "String", "Value": "val1"}}}'
        }]

        result = parser.parse_messages(messages)

        assert len(result) == 1
        assert result[0]["message_id"] == "msg-123"
        assert result[0]["receipt_handle"] == "handle-123"
        assert result[0]["message_contents"] == {"key": "value"}
        assert result[0]["message_attributes"] == {"attr1": {"Type": "String", "Value": "val1"}}

    @patch('src.utils.queue.sqs.sqs_message_parser.Logger')
    def test_parse_direct_sqs_message(self, mock_logger):
        parser = SQSMessageParser()

        messages = [{
            "MessageId": "msg-456",
            "ReceiptHandle": "handle-456",
            "Body": '{"key": "value"}',
            "MessageAttributes": {"attr1": {"StringValue": "val1"}}
        }]

        result = parser.parse_messages(messages)

        assert len(result) == 1
        assert result[0]["message_contents"] == {"key": "value"}

    @patch('src.utils.queue.sqs.sqs_message_parser.Logger')
    def test_skip_message_without_body(self, mock_logger):
        parser = SQSMessageParser()

        messages = [{"MessageId": "msg-789"}]

        result = parser.parse_messages(messages)
        assert len(result) == 0

    @patch('src.utils.queue.sqs.sqs_message_parser.Logger')
    def test_skip_invalid_json(self, mock_logger):
        parser = SQSMessageParser()

        messages = [{
            "MessageId": "msg-invalid",
            "ReceiptHandle": "handle-invalid",
            "Body": "not valid json"
        }]

        result = parser.parse_messages(messages)
        assert len(result) == 0

    @patch('src.utils.queue.sqs.sqs_message_parser.Logger')
    def test_parse_multiple_messages(self, mock_logger):
        parser = SQSMessageParser()

        messages = [
            {
                "MessageId": "msg-1",
                "ReceiptHandle": "handle-1",
                "Body": '{"data": "first"}'
            },
            {
                "MessageId": "msg-2",
                "ReceiptHandle": "handle-2",
                "Body": '{"data": "second"}'
            }
        ]

        result = parser.parse_messages(messages)

        assert len(result) == 2
        assert result[0]["message_contents"]["data"] == "first"
        assert result[1]["message_contents"]["data"] == "second"


class TestQueueMessageHandler:
    @patch('src.utils.queue.queue_message_handler.get_config_service')
    @patch('src.utils.queue.queue_message_handler.Logger')
    def test_handler_initialization(self, mock_logger, mock_get_config):
        mock_appconfig = MagicMock()
        mock_appconfig.get.return_value = 5
        mock_get_config.return_value = mock_appconfig

        mock_message_handler = MagicMock(spec=MessageHandler)
        handler = QueueMessageHandler(mock_message_handler, max_worker_count=5)

        assert handler.max_worker_count == 5
        handler.close()

    @patch('src.utils.queue.queue_message_handler.get_config_service')
    @patch('src.utils.queue.queue_message_handler.Logger')
    def test_handler_uses_appconfig_default(self, mock_logger, mock_get_config):
        mock_appconfig = MagicMock()
        mock_appconfig.get.return_value = 10
        mock_get_config.return_value = mock_appconfig

        mock_message_handler = MagicMock(spec=MessageHandler)
        handler = QueueMessageHandler(mock_message_handler)

        assert handler.max_worker_count == 10
        handler.close()

    @patch('src.utils.queue.queue_message_handler.get_config_service')
    @patch('src.utils.queue.queue_message_handler.Logger')
    def test_handler_delegates_to_message_handler(self, mock_logger, mock_get_config):
        mock_appconfig = MagicMock()
        mock_appconfig.get.return_value = 2
        mock_get_config.return_value = mock_appconfig

        mock_message_handler = MagicMock(spec=MessageHandler)
        mock_message_handler.handle.return_value = True

        handler = QueueMessageHandler(mock_message_handler, max_worker_count=2)
        future = handler.submit({"test": "data"})

        result = future.result(timeout=5)
        assert result is True
        mock_message_handler.handle.assert_called_once()

        handler.close()

    @patch('src.utils.queue.queue_message_handler.get_config_service')
    @patch('src.utils.queue.queue_message_handler.Logger')
    def test_submit_returns_future(self, mock_logger, mock_get_config):
        mock_appconfig = MagicMock()
        mock_appconfig.get.return_value = 2
        mock_get_config.return_value = mock_appconfig

        mock_message_handler = MagicMock(spec=MessageHandler)
        mock_message_handler.handle.return_value = True

        handler = QueueMessageHandler(mock_message_handler, max_worker_count=2)
        future = handler.submit({"test": "data"})

        assert isinstance(future, Future)
        assert future.result(timeout=5) is True
        handler.close()

    @patch('src.utils.queue.queue_message_handler.get_config_service')
    @patch('src.utils.queue.queue_message_handler.Logger')
    def test_submit_catches_handler_exceptions(self, mock_logger, mock_get_config):
        mock_appconfig = MagicMock()
        mock_appconfig.get.return_value = 2
        mock_get_config.return_value = mock_appconfig

        mock_message_handler = MagicMock(spec=MessageHandler)
        mock_message_handler.handle.side_effect = ValueError("Test error")

        handler = QueueMessageHandler(mock_message_handler, max_worker_count=2)
        future = handler.submit({"test": "data"})

        # Should not raise, returns True on error
        result = future.result(timeout=5)
        assert result is True
        handler.close()


class TestQueueVisibilityExtender:
    @patch('src.utils.queue.sqs.sqs_visibility_extender.get_config_service')
    @patch('src.utils.queue.sqs.sqs_visibility_extender.Logger')
    @patch('src.utils.queue.sqs.sqs_visibility_extender.get_sqs_service')
    def test_register_message(self, mock_sqs, mock_logger, mock_get_config):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "sqs.visibility_extension_interval_seconds": 30,
            "sqs.visibility_timeout_seconds": 300,
            "sqs.max_message_process_time_seconds": 600,
            "sqs.queue_url": "https://test-queue",
            "sqs.consumer_shutdown_timeout_seconds": 30
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        from src.utils.queue.sqs.sqs_visibility_extender import SQSVisibilityExtender

        extender = SQSVisibilityExtender()

        extender.register_message("msg-123", "handle-123")

        assert extender.is_message_registered("msg-123") is True
        assert extender.is_message_registered("msg-456") is False

    @patch('src.utils.queue.sqs.sqs_visibility_extender.get_config_service')
    @patch('src.utils.queue.sqs.sqs_visibility_extender.Logger')
    @patch('src.utils.queue.sqs.sqs_visibility_extender.get_sqs_service')
    def test_unregister_message(self, mock_sqs, mock_logger, mock_get_config):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "sqs.visibility_extension_interval_seconds": 30,
            "sqs.visibility_timeout_seconds": 300,
            "sqs.max_message_process_time_seconds": 600,
            "sqs.queue_url": "https://test-queue",
            "sqs.consumer_shutdown_timeout_seconds": 30
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        from src.utils.queue.sqs.sqs_visibility_extender import SQSVisibilityExtender

        extender = SQSVisibilityExtender()

        extender.register_message("msg-123", "handle-123")
        metadata = extender.unregister_message("msg-123")

        assert metadata is not None
        assert metadata["receipt_handle"] == "handle-123"
        assert extender.is_message_registered("msg-123") is False

    @patch('src.utils.queue.sqs.sqs_visibility_extender.get_config_service')
    @patch('src.utils.queue.sqs.sqs_visibility_extender.Logger')
    @patch('src.utils.queue.sqs.sqs_visibility_extender.get_sqs_service')
    def test_duplicate_registration_raises(self, mock_sqs, mock_logger, mock_get_config):
        mock_appconfig = MagicMock()
        mock_appconfig.get.side_effect = lambda key, default=None: {
            "sqs.visibility_extension_interval_seconds": 30,
            "sqs.visibility_timeout_seconds": 300,
            "sqs.max_message_process_time_seconds": 600,
            "sqs.queue_url": "https://test-queue",
            "sqs.consumer_shutdown_timeout_seconds": 30
        }.get(key, default)
        mock_get_config.return_value = mock_appconfig

        from src.utils.queue.sqs.sqs_visibility_extender import SQSVisibilityExtender

        extender = SQSVisibilityExtender()

        extender.register_message("msg-123", "handle-123")

        with pytest.raises(ValueError):
            extender.register_message("msg-123", "handle-456")
