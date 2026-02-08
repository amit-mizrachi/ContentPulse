"""Integration tests for SQS message parsing.

Tests verify correct parsing of:
- SNS-wrapped SQS messages
- Direct SQS messages
- Batch message processing with mixed formats
"""
import json
import pytest
from unittest.mock import patch


class TestSnsWrappedMessages:
    """Tests for SNS-wrapped SQS message parsing."""

    @patch('src.utils.queue.sqs.sqs_message_parser.Logger')
    def test_parses_sns_wrapped_message(self, mock_logger):
        """Parser should correctly unwrap SNS messages."""
        from src.utils.queue.sqs.sqs_message_parser import SQSMessageParser

        parser = SQSMessageParser()

        messages = [{
            "MessageId": "msg-123",
            "ReceiptHandle": "handle-123",
            "Body": json.dumps({
                "Message": json.dumps({
                    "request_id": "test-123",
                    "topic_name": "inference",
                    "judge_request": {"prompt": "test"}
                }),
                "MessageAttributes": {"attr1": {"Type": "String", "Value": "val1"}}
            })
        }]

        result = parser.parse_messages(messages)

        assert len(result) == 1
        assert result[0]["message_contents"]["request_id"] == "test-123"
        assert result[0]["message_contents"]["topic_name"] == "inference"

    @patch('src.utils.queue.sqs.sqs_message_parser.Logger')
    def test_extracts_sns_message_attributes(self, mock_logger):
        """Parser should extract SNS message attributes."""
        from src.utils.queue.sqs.sqs_message_parser import SQSMessageParser

        parser = SQSMessageParser()

        messages = [{
            "MessageId": "msg-123",
            "ReceiptHandle": "handle-123",
            "Body": json.dumps({
                "Message": json.dumps({"data": "test"}),
                "MessageAttributes": {
                    "TraceId": {"Type": "String", "Value": "trace-abc"},
                    "RequestId": {"Type": "String", "Value": "req-123"}
                }
            })
        }]

        result = parser.parse_messages(messages)

        assert result[0]["message_attributes"]["TraceId"]["Value"] == "trace-abc"
        assert result[0]["message_attributes"]["RequestId"]["Value"] == "req-123"


class TestDirectSqsMessages:
    """Tests for direct SQS message parsing."""

    @patch('src.utils.queue.sqs.sqs_message_parser.Logger')
    def test_parses_direct_sqs_message(self, mock_logger):
        """Parser should correctly parse direct SQS messages."""
        from src.utils.queue.sqs.sqs_message_parser import SQSMessageParser

        parser = SQSMessageParser()

        messages = [{
            "MessageId": "msg-456",
            "ReceiptHandle": "handle-456",
            "Body": json.dumps({
                "request_id": "test-456",
                "data": "direct message"
            })
        }]

        result = parser.parse_messages(messages)

        assert len(result) == 1
        assert result[0]["message_contents"]["request_id"] == "test-456"
        assert result[0]["message_contents"]["data"] == "direct message"

    @patch('src.utils.queue.sqs.sqs_message_parser.Logger')
    def test_extracts_direct_message_attributes(self, mock_logger):
        """Parser should extract direct SQS message attributes."""
        from src.utils.queue.sqs.sqs_message_parser import SQSMessageParser

        parser = SQSMessageParser()

        messages = [{
            "MessageId": "msg-456",
            "ReceiptHandle": "handle-456",
            "Body": json.dumps({"data": "test"}),
            "MessageAttributes": {
                "CustomAttr": {"StringValue": "custom-value"}
            }
        }]

        result = parser.parse_messages(messages)

        assert result[0]["message_attributes"]["CustomAttr"]["StringValue"] == "custom-value"


class TestBatchMessageProcessing:
    """Tests for batch message processing with mixed formats."""

    @patch('src.utils.queue.sqs.sqs_message_parser.Logger')
    def test_processes_mixed_valid_messages(self, mock_logger):
        """Parser should process batch with mixed message formats."""
        from src.utils.queue.sqs.sqs_message_parser import SQSMessageParser

        parser = SQSMessageParser()

        messages = [
            {
                "MessageId": "msg-1",
                "ReceiptHandle": "handle-1",
                "Body": json.dumps({
                    "Message": json.dumps({"type": "sns-wrapped"}),
                    "MessageAttributes": {}
                })
            },
            {
                "MessageId": "msg-2",
                "ReceiptHandle": "handle-2",
                "Body": json.dumps({"type": "direct"})
            }
        ]

        result = parser.parse_messages(messages)

        assert len(result) == 2
        assert result[0]["message_contents"]["type"] == "sns-wrapped"
        assert result[1]["message_contents"]["type"] == "direct"

    @patch('src.utils.queue.sqs.sqs_message_parser.Logger')
    def test_skips_invalid_messages_in_batch(self, mock_logger):
        """Parser should skip invalid messages and continue processing."""
        from src.utils.queue.sqs.sqs_message_parser import SQSMessageParser

        parser = SQSMessageParser()

        messages = [
            {
                "MessageId": "msg-1",
                "ReceiptHandle": "handle-1",
                "Body": json.dumps({"valid": "message"})
            },
            {
                "MessageId": "msg-2",
                "ReceiptHandle": "handle-2",
                "Body": "invalid json {"
            },
            {
                "MessageId": "msg-3"
                # Missing Body
            },
            {
                "MessageId": "msg-4",
                "ReceiptHandle": "handle-4",
                "Body": json.dumps({"another": "valid"})
            }
        ]

        result = parser.parse_messages(messages)

        assert len(result) == 2
        assert result[0]["message_contents"]["valid"] == "message"
        assert result[1]["message_contents"]["another"] == "valid"

    @patch('src.utils.queue.sqs.sqs_message_parser.Logger')
    def test_preserves_message_metadata(self, mock_logger):
        """Parser should preserve message ID and receipt handle."""
        from src.utils.queue.sqs.sqs_message_parser import SQSMessageParser

        parser = SQSMessageParser()

        messages = [
            {
                "MessageId": "unique-msg-id",
                "ReceiptHandle": "unique-receipt-handle",
                "Body": json.dumps({"data": "test"})
            }
        ]

        result = parser.parse_messages(messages)

        assert result[0]["message_id"] == "unique-msg-id"
        assert result[0]["receipt_handle"] == "unique-receipt-handle"


class TestMessageParsingEdgeCases:
    """Tests for edge cases in message parsing."""

    @patch('src.utils.queue.sqs.sqs_message_parser.Logger')
    def test_handles_empty_message_batch(self, mock_logger):
        """Parser should handle empty message batch."""
        from src.utils.queue.sqs.sqs_message_parser import SQSMessageParser

        parser = SQSMessageParser()

        result = parser.parse_messages([])

        assert result == []

    @patch('src.utils.queue.sqs.sqs_message_parser.Logger')
    def test_handles_nested_json_in_sns_message(self, mock_logger):
        """Parser should handle deeply nested JSON in SNS messages."""
        from src.utils.queue.sqs.sqs_message_parser import SQSMessageParser

        parser = SQSMessageParser()

        nested_data = {
            "request_id": "test-123",
            "nested": {
                "level1": {
                    "level2": {
                        "data": "deeply nested"
                    }
                }
            }
        }

        messages = [{
            "MessageId": "msg-nested",
            "ReceiptHandle": "handle-nested",
            "Body": json.dumps({
                "Message": json.dumps(nested_data),
                "MessageAttributes": {}
            })
        }]

        result = parser.parse_messages(messages)

        assert result[0]["message_contents"]["nested"]["level1"]["level2"]["data"] == "deeply nested"

    @patch('src.utils.queue.sqs.sqs_message_parser.Logger')
    def test_handles_unicode_in_messages(self, mock_logger):
        """Parser should handle unicode characters in messages."""
        from src.utils.queue.sqs.sqs_message_parser import SQSMessageParser

        parser = SQSMessageParser()

        messages = [{
            "MessageId": "msg-unicode",
            "ReceiptHandle": "handle-unicode",
            "Body": json.dumps({
                "prompt": "What is 2+2? 你好 🎉",
                "response": "The answer is 4. Привет! 日本語"
            })
        }]

        result = parser.parse_messages(messages)

        assert "你好" in result[0]["message_contents"]["prompt"]
        assert "🎉" in result[0]["message_contents"]["prompt"]
        assert "Привет" in result[0]["message_contents"]["response"]
