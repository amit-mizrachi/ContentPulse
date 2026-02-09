"""AWS SQS message consumer service."""
from functools import lru_cache

import boto3

from src.shared.observability.logs.logger import Logger
from src.shared.appconfig_client import get_config_service


class SQSClient:
    def __init__(self):
        self._appconfig = get_config_service()
        self._sqs_client = boto3.client(
            "sqs",
            region_name=self._appconfig.get("clients.region")
        )
        self._logger = Logger()

    def receive_message(self, queue_url: str):
        try:
            visibility_timeout = self._appconfig.get("sqs.visibility_timeout_seconds")
            wait_time = self._appconfig.get("sqs.wait_time_seconds")

            http_response = self._sqs_client.receive_message(
                QueueUrl=queue_url,
                VisibilityTimeout=visibility_timeout,
                WaitTimeSeconds=wait_time,
                MessageAttributeNames=["All"]
            )

            return http_response.get("Messages", [])
        except Exception as e:
            self._logger.error(f"Failed to receive message from SQS queue: {e}")
            raise

    def change_message_visibility(self, queue_url: str, message_handle: str, visibility_timeout: int):
        try:
            self._sqs_client.change_message_visibility(
                QueueUrl=queue_url,
                ReceiptHandle=message_handle,
                VisibilityTimeout=visibility_timeout
            )
        except Exception as e:
            self._logger.error(f"Failed to change SQS message visibility timeout: {e}")
            raise

    def delete_message(self, queue_url: str, message_handle: str):
        try:
            return self._sqs_client.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=message_handle
            )
        except Exception as e:
            self._logger.error(f"Failed to delete message from SQS queue: {e}")
            raise


@lru_cache(maxsize=1)
def get_sqs_service() -> SQSClient:
    """Get the singleton SQSService instance."""
    return SQSClient()
