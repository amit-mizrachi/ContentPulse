import asyncio
import functools
from asyncio import BoundedSemaphore
from concurrent.futures import Future
from typing import Optional

from src.shared.aws.appconfig_service import get_config_service
from src.shared.aws.sqs_service import get_sqs_service
from src.shared.observability.logs.logger import Logger
from src.shared.observability.traces.spans.span_context_factory import SpanContextFactory
from src.shared.observability.traces.spans.spanner import Spanner
from src.shared.interfaces.messaging.message_dispatcher import MessageDispatcher
from src.shared.messaging.sqs.sqs_visibility_extender import SQSVisibilityExtender


class MessageAlreadyProcessingError(Exception):
    def __init__(self, message_id: str):
        self.message_id = message_id
        super().__init__(f"Message {message_id} is already being processed")


class SQSMessageProcessor:
    def __init__(
        self,
        visibility_extender: SQSVisibilityExtender,
        message_handler: MessageDispatcher,
        queue_config_key: str = "sqs.queue_url"
    ):
        self.__appconfig = get_config_service()
        self.__logger = Logger()
        self.__sqs_service = get_sqs_service()

        self.__visibility_extender = visibility_extender
        self.__message_handler = message_handler
        self.__queue_url = self.__appconfig.get(queue_config_key)

        self.__spanner = Spanner()
        self.__semaphore = BoundedSemaphore(message_handler.max_worker_count)
        self.__event_loop: Optional[asyncio.AbstractEventLoop] = None
        self.__closed = False

    def set_event_loop(self, event_loop: asyncio.AbstractEventLoop):
        self.__event_loop = event_loop

    async def acquire_slot(self):
        await self.__semaphore.acquire()

    async def process_message(self, parsed_message: dict):
        message_id = parsed_message["message_id"]
        receipt_handle = parsed_message["receipt_handle"]
        message_contents = parsed_message["message_contents"]

        try:
            message_result = await self.__process_message(receipt_handle, message_id, message_contents)
            self.__finalize_message(message_id, message_result)
        except MessageAlreadyProcessingError:
            self.__release_slot()
        except Exception as e:
            self.__logger.error(f"Failed to process message {message_id}: {e}")
            self.__release_slot()

    async def __process_message(self, receipt_handle: str, message_id: str, message_contents: dict):
        try:
            if self.__visibility_extender.is_message_registered(message_id):
                raise MessageAlreadyProcessingError(message_id)

            self.__visibility_extender.register_message(message_id, receipt_handle)

            telemetry_headers = message_contents.get("telemetry_headers", {})
            telemetry_context = self.__spanner.extract_telemetry_context(telemetry_headers)

            with SpanContextFactory.consumer(self.__queue_url, message_id, message_contents, telemetry_context=telemetry_context):
                message_result = self.__message_handler.submit(message_contents)
            return message_result
        except MessageAlreadyProcessingError:
            self.__logger.warning(f"Message {message_id} is already being processed")
            raise
        except Exception as e:
            self.__logger.error(f"Could not submit queue message to message handler: {e}")
            self.__visibility_extender.unregister_message(message_id)
            raise

    def __finalize_message(self, message_id: str, delete_message_future: Future):
        if isinstance(delete_message_future, Future):
            delete_message_future.add_done_callback(
                functools.partial(
                    self.__process_message_result,
                    message_id,
                    delete_message_future
                )
            )
        elif delete_message_future is not None:
            self.__process_message_result(message_id, delete_message_future)

    def __process_message_result(self, message_id: str, delete_message_future: Future, *args, **kwargs):
        try:
            delete_message_flag = delete_message_future.result() if isinstance(delete_message_future, Future) else delete_message_future
            if delete_message_flag:
                self.__delete_message_by_id(message_id)
            else:
                self.__logger.info("Postponing message deletion to next cycle")
        except Exception as e:
            self.__logger.error(f"Error processing message result: {e}")
        finally:
            self.__release_slot()

    def _has_event_loop(self) -> bool:
        return self.__event_loop is not None

    def __release_slot(self):
        if self._has_event_loop():
            self.__event_loop.call_soon_threadsafe(self.__do_release_semaphore)

    def __do_release_semaphore(self):
        try:
            self.__semaphore.release()
        except ValueError:
            self.__logger.warning("Semaphore released more times than acquired")
        except Exception:
            self.__logger.warning("Failed to release semaphore")

    def __delete_message_by_id(self, message_id: str):
        try:
            message_metadata = self.__visibility_extender.unregister_message(message_id)
            if message_metadata is None:
                self.__logger.warning("No message with the given ID is currently being processed")
                return

            self.__delete_message_by_handle(message_metadata["receipt_handle"])
        except Exception as e:
            self.__logger.error(f"Failed to delete message from queue: {e}")

    def __delete_message_by_handle(self, receipt_handle: str):
        try:
            self.__sqs_service.delete_message(
                queue_url=self.__queue_url,
                message_handle=receipt_handle
            )
        except Exception as e:
            self.__logger.error(f"Failed to delete message from queue: {e}")

    def close(self):
        self.__closed = True

    @property
    def closed(self):
        return self.__closed
