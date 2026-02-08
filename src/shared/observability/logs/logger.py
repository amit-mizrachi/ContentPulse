import json
import logging
import sys
import traceback
from typing import Optional

from opentelemetry.trace import StatusCode

from src.shared.observability.logs.buffered_file_handler import BufferedFileHandler
from src.shared.observability.observability_base import ObservabilityBase


class Logger(ObservabilityBase):
    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger("norman_logger")

        if not self._logger.handlers:
            self._configure_logger()

    def _configure_logger(self):
        try:
            self._setup_file_handler()
            self._setup_stdout_handler()

            min_level = self._appconfig_service.get("observability.logs.minimum_logging_levels.logger")
            self._logger.setLevel(min_level)
        except Exception:
            print("Failed to initialize Logger", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)

    def _setup_file_handler(self):
        base_path = self._appconfig_service.get("observability.logs.files.path")
        capacity = int(self._appconfig_service.get("observability.logs.files.buffer_capacity"))
        min_level = self._appconfig_service.get("observability.logs.minimum_logging_levels.files_handler")

        path = f"{base_path}/{self._service_name}.log"
        handler = BufferedFileHandler(path, buffer_capacity=capacity)
        handler.setLevel(min_level)
        self._logger.addHandler(handler)

    def _setup_stdout_handler(self):
        min_level = self._appconfig_service.get("observability.logs.minimum_logging_levels.stdout_handler")
        fmt = logging.Formatter("[%(asctime)s][%(levelname)s][Logger %(name)s][PID %(process)d]: %(message)s")

        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setLevel(min_level)
        handler.setFormatter(fmt)
        self._logger.addHandler(handler)

    def debug(self, message: str, *args, **kwargs):
        return self._log(logging.DEBUG, message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        return self._log(logging.INFO, message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        return self._log(logging.WARNING, message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        msg = self._log(logging.ERROR, message, *args, **kwargs)
        self._record_span_error(logging.ERROR, msg)
        return msg

    def critical(self, message: str, *args, **kwargs):
        msg = self._log(logging.CRITICAL, message, *args, **kwargs)
        self._record_span_error(logging.CRITICAL, msg)
        return msg

    def flush(self):
        for handler in self._logger.handlers:
            handler.flush()

    def shutdown(self):
        logging.shutdown()

    def _log(self, level: int, message: str, *args, **kwargs) -> str:
        payload = self._build_log_payload(level, message)

        try:
            self._logger.log(level=level, msg=payload, *args, **kwargs)
        except Exception as e:
            print(f"Logger failure: {message} | Error: {e}", file=sys.stderr)

        return message

    def _build_log_payload(self, level: int, message: str) -> str:
        trace_id, span_id = self._get_trace_context()

        obj = {
            "level": logging.getLevelName(level),
            "message": message,
            "trace_id": trace_id,
            "span_id": span_id,
            "log_type": "norman_logs",
            "environment": self._appconfig_service.get("environment", self._default_attribute),
            "sandbox": self._appconfig_service.get("norman_sandbox", self._default_attribute),
            "service_name": self._service_name,
        }
        return json.dumps(obj, default=str)

    def _get_trace_context(self) -> tuple[Optional[str], Optional[str]]:
        try:
            ctx = self.get_current_span().get_span_context()
            return ctx.trace_id, ctx.span_id
        except Exception:
            return None, None

    def _record_span_error(self, level: int, message: str):
        level_name = logging.getLevelName(level)
        attrs = {
            "log.severity": level_name,
            "log.message": message,
        }
        self.add_current_span_event(level_name, attrs, StatusCode.ERROR)
