import os

import opentelemetry.context
import opentelemetry.propagate
import opentelemetry.trace

from src.utils.services.aws.appconfig_service import get_config_service
from src.utils.observability.constants import DEFAULT_ATTRIBUTE
from src.utils.singleton import Singleton


class ObservabilityBase(metaclass=Singleton):
    _default_attribute = DEFAULT_ATTRIBUTE

    def __init__(self):
        self._appconfig_service = get_config_service()
        self._service_name = os.getcwd().split(os.sep)[-1]

    def get_current_span(self):
        current_span = opentelemetry.trace.get_current_span()
        return current_span

    def add_current_span_event(self, event_name: str, event_attributes: dict, status_code: opentelemetry.trace.StatusCode):
        span = self.get_current_span()
        if span is not None and span.get_span_context().is_valid and span.is_recording():
            span.add_event(name=event_name, attributes=event_attributes)
            span.set_status(opentelemetry.trace.Status(status_code))
