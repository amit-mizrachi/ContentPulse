import threading
import time
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Optional, Any

from src.utils.services.aws.appconfig_service import get_config_service
from src.utils.services.aws.sqs_service import get_sqs_service
from src.utils.observability.logs.logger import Logger


class SQSVisibilityExtender:
    def __init__(self, queue_config_key: str = "sqs.queue_url"):
        self.__appconfig = get_config_service()
        self.__logger = Logger()
        self.__sqs_service = get_sqs_service()

        self.__extension_interval = self.__appconfig.get("sqs.visibility_extension_interval_seconds", 30)
        self.__visibility_timeout = self.__appconfig.get("sqs.visibility_timeout_seconds", 300)
        self.__max_processing_time = self.__appconfig.get("sqs.max_message_process_time_seconds", 600)
        self.__queue_url = self.__appconfig.get(queue_config_key)
        self.__shutdown_timeout = self.__appconfig.get("sqs.consumer_shutdown_timeout_seconds", 30)

        self.__messages_being_processed: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self.__messages_lock = threading.Lock()
        self.__thread: Optional[threading.Thread] = None
        self.__closed = False

    def start(self):
        self.__thread = threading.Thread(target=self.__extension_loop, daemon=True)
        self.__thread.start()

    def __extension_loop(self):
        while not self.__closed:
            try:
                time.sleep(self.__extension_interval)

                if self.__closed:
                    break

                self.__extend_visibility_for_all_messages()
            except Exception as e:
                self.__logger.error(f"Error in visibility extension loop: {e}")

    def __extend_visibility_for_all_messages(self):
        now = datetime.now(timezone.utc)
        messages_to_extend = []

        with self.__messages_lock:
            for message_id, message_metadata in self.__messages_being_processed.items():
                time_since_last_extension = (now - message_metadata["last_visibility_extension"]).total_seconds()
                if time_since_last_extension < self.__extension_interval:
                    break

                processing_duration = (now - message_metadata["started_at"]).total_seconds()

                if processing_duration > self.__max_processing_time:
                    self.__logger.error(f"Message {message_id} exceeded max processing time, will not extend visibility")
                else:
                    messages_to_extend.append((message_id, message_metadata["receipt_handle"]))

        for message_id, receipt_handle in messages_to_extend:
            try:
                self.__logger.debug(f"Extending visibility timeout for message {message_id}")
                self.__sqs_service.change_message_visibility(
                    self.__queue_url,
                    receipt_handle,
                    self.__visibility_timeout
                )

                with self.__messages_lock:
                    if message_id in self.__messages_being_processed:
                        self.__messages_being_processed[message_id]["last_visibility_extension"] = now
                        self.__messages_being_processed.move_to_end(message_id)

            except Exception as e:
                self.__logger.warning(f"Failed to extend visibility for message {message_id}: {e}")

    def is_message_registered(self, message_id: str):
        with self.__messages_lock:
            return message_id in self.__messages_being_processed

    def register_message(self, message_id: str, receipt_handle: str):
        with self.__messages_lock:
            if message_id in self.__messages_being_processed:
                raise ValueError(f"Message {message_id} is already being processed.")

            now = datetime.now(timezone.utc)
            self.__messages_being_processed[message_id] = {
                "receipt_handle": receipt_handle,
                "started_at": now,
                "last_visibility_extension": now,
            }

    def unregister_message(self, message_id: str):
        with self.__messages_lock:
            return self.__messages_being_processed.pop(message_id, None)

    def close(self):
        self.__closed = True
        if self.__thread is not None and self.__thread.is_alive():
            self.__thread.join(timeout=self.__shutdown_timeout)

    @property
    def closed(self):
        return self.__closed
