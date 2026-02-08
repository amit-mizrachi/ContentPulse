import json

from src.shared.observability.logs.logger import Logger


class SQSMessageParser:
    def __init__(self):
        self.__logger = Logger()

    def parse_messages(self, messages: list[dict]) -> list[dict]:
        parsed_messages = []

        for message in messages:
            try:
                if "Body" not in message:
                    self.__logger.warning("Skipping message: 'Body' key is missing")
                    continue

                body = json.loads(message["Body"])

                if "Message" in body:
                    message_contents = json.loads(body["Message"])
                    message_attributes = body.get("MessageAttributes")
                else:
                    message_contents = body
                    message_attributes = message.get("MessageAttributes")

                parsed_messages.append({
                    "message_id": message.get("MessageId"),
                    "receipt_handle": message.get("ReceiptHandle"),
                    "message_contents": message_contents,
                    "message_attributes": message_attributes
                })

            except json.JSONDecodeError as e:
                self.__logger.warning(f"Skipping queue message due to JSON decode error: {e}")
                continue
            except Exception as e:
                self.__logger.warning(f"Skipping queue message due to error: {e}")
                continue

        return parsed_messages
