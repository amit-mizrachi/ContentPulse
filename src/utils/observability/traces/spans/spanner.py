from typing import Any, Optional

import opentelemetry.context
import opentelemetry.propagate
import opentelemetry.trace

from src.utils.observability.logs.logger import Logger
from src.utils.observability.observability_base import ObservabilityBase


class Spanner(ObservabilityBase):
    def __init__(self):
        super().__init__()
        self.__logger = Logger()
        self.__tracer = opentelemetry.trace.get_tracer(self._service_name)

    def start_span(
        self,
        name: str,
        kind: opentelemetry.trace.SpanKind,
        attributes: dict[str, Any],
        telemetry_context: Optional[opentelemetry.context.Context] = None,
        get_telemetry_context_if_none: Optional[bool] = True
    ):
        try:
            if telemetry_context is None and get_telemetry_context_if_none:
                telemetry_context = self.get_telemetry_context()

            span = self.__tracer.start_span(
                name=name,
                context=telemetry_context,
                kind=kind,
                attributes=attributes
            )
            
            return span 
        except Exception as e:
            self.__logger.error("Failed to start span")
            cause = str(e)
            self.__logger.debug(cause)
            raise e

    def end_span(self, span: opentelemetry.trace.Span, *args, **kwargs): # Args and kwargs are added so we are able to end spans asynchronically
        try:
            span.end()
        except Exception as e:
            self.__logger.error("Failed to end span")
            cause = str(e)
            self.__logger.debug(cause)
            raise e

    def use_span_context_manager(self,
        span: opentelemetry.trace.Span,
        end_on_exit: bool = True,
        record_exception: bool = True,
        set_status_on_exception: bool = True
    ):
        try:
            span_context_manager = opentelemetry.trace.use_span(
                span,
                end_on_exit,
                record_exception,
                set_status_on_exception
            ) 
            
            return span_context_manager 
        except Exception as e:
            self.__logger.error("Failed to use span")
            cause = str(e)
            self.__logger.debug(cause)
            raise e

    def get_telemetry_context(self):
        telemetry_context = opentelemetry.context.get_current()
        return telemetry_context

    def inject_telemetry_context(self, carrier: Any):
        opentelemetry.propagate.inject(carrier)
        return carrier

    def extract_telemetry_context(self, carrier: Any):
        telemetry_context = opentelemetry.propagate.extract(carrier)
        return telemetry_context
