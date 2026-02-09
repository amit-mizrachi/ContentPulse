from src.shared.interfaces.messaging.message_handler import MessageHandler
from src.shared.interfaces.messaging.message_dispatcher import MessageDispatcher
from src.shared.aws.appconfig_service import get_config_service
from src.shared.observability.logs.logger import Logger
from src.shared.messaging.context_preserving_thread_pool import ContextPreservingThreadPool


class ThreadPoolMessageDispatcher(MessageDispatcher):
    def __init__(self, handler: MessageHandler, max_worker_count: int = None):
        self.__appconfig = get_config_service()
        self.__logger = Logger()
        self._handler = handler

        if max_worker_count is None:
            max_worker_count = self.__appconfig.get("sqs.max_worker_count", 10)

        self._handle_pool = ContextPreservingThreadPool(max_workers=max_worker_count)
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
