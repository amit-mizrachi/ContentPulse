"""AWS SNS message publisher service."""
from functools import lru_cache

import boto3

from src.interfaces.message_publisher import MessagePublisher
from src.utils.observability.logs.logger import Logger
from src.utils.services.aws.appconfig_service import get_config_service


class SNSService(MessagePublisher):
    """AWS SNS message publisher."""

    def __init__(self):
        self._appconfig = get_config_service()
        self._sns_client = boto3.client(
            "sns",
            region_name=self._appconfig.get("aws.region")
        )
        self._logger = Logger()
        self._topic_map = {
            "inference": self._appconfig.get("sns.inference_topic_arn"),
            "judge": self._appconfig.get("sns.judge_topic_arn"),
        }

    def publish(self, topic_name: str, message: str) -> bool:
        topic_arn = self._topic_map.get(topic_name, topic_name)
        try:
            publish_args = {
                "TopicArn": topic_arn,
                "Message": message,
            }

            response = self._sns_client.publish(**publish_args)

            status_code = response.get("ResponseMetadata", {}).get("HTTPStatusCode", 0)
            if status_code != 200:
                raise Exception(f"SNS publish failed with status {status_code}")

            self._logger.info(f"Published message to {topic_arn}")
            return True
        except Exception as e:
            self._logger.error(f"Failed to send message to SNS topic {topic_arn}: {e}")
            raise e


@lru_cache(maxsize=1)
def get_sns_service() -> SNSService:
    """Get the singleton SNSService instance."""
    return SNSService()
