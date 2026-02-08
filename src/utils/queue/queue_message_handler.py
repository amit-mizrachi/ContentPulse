from src.interfaces.message_handler import MessageHandler
from src.utils.services.aws.appconfig_service import get_config_service
from src.utils.observability.logs.logger import Logger
from src.utils.queue.context_preserving_executor import ContextPreservingExecutor


class QueueMessageHandler:
    def __init__(self, handler: MessageHandler, max_worker_count: int = None):
        self.__appconfig = get_config_service()
        self.__logger = Logger()
        self._handler = handler

        if max_worker_count is None:
            max_worker_count = self.__appconfig.get("sqs.max_worker_count", 10)

        self._handle_pool = ContextPreservingExecutor(max_workers=max_worker_count)
        self._max_worker_count = max_worker_count
        self._closed = False

    def submit(self, raw_message, *args, **kwargs):
        try:
            return self._handle_pool.submit(self.__secure_handle, raw_message, *args, **kwargs)
        except Exception:
            return True

    def __secure_handle(self, raw_message, *args, **kwargs):
        try:
            return self._handler.handle(raw_message, *args, **kwargs)
        except Exception as e:
            self.__logger.error(f"Failed to handle queue message: {e}")
            return True

    @property
    def max_worker_count(self):
        return self._max_worker_count

    def close(self, *args, **kwargs):
        self._handle_pool.shutdown(cancel_futures=True)
        self._closed = True
