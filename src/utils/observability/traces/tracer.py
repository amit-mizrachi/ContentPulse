import opentelemetry.exporter.otlp.proto.http.trace_exporter
import opentelemetry.sdk.resources
import opentelemetry.sdk.trace.export
import opentelemetry.sdk.trace.sampling
import opentelemetry.trace

from src.utils.observability.logs.logger import Logger
from src.utils.observability.observability_base import ObservabilityBase


class Tracer(ObservabilityBase):
    def __init__(self):
        super().__init__()
        try:
            self.__logger = Logger()

            environment = self._appconfig_service.get("environment")
            resource_attributes = {
                "deployment.environment": environment,
                "service.name": self._service_name
            }

            resource = opentelemetry.sdk.resources.Resource.create(attributes=resource_attributes)
            trace_sample_rate = self._appconfig_service.get("observability.traces.sample_rate")
            self.__sampler = opentelemetry.sdk.trace.sampling.TraceIdRatioBased(trace_sample_rate)

            self.__tracer_provider = opentelemetry.sdk.trace.TracerProvider(
                resource=resource,
                sampler=self.__sampler,
            )

            tracer_endpoint = self._appconfig_service.get("observability.traces.collector.endpoint")
            span_exporter = (opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter(endpoint=tracer_endpoint))
            span_processor = (opentelemetry.sdk.trace.export.BatchSpanProcessor(span_exporter))

            self.__tracer_provider.add_span_processor(span_processor)
            opentelemetry.trace.set_tracer_provider(self.__tracer_provider)

        except Exception as e:
            self.__logger.error("Failed to initialize Tracer")
            cause = str(e)
            self.__logger.debug(cause)
            raise e

    def flush(self):
        try:
            flush_timeout_ms = self._appconfig_service.get("observability.traces.tracer_flush_timeout_ms")
            self.__tracer_provider.force_flush(timeout_millis=flush_timeout_ms)
        except Exception as e:
            self.__logger.error("Force flush failed")
            cause = str(e)
            self.__logger.debug(cause)
            raise e

    def shutdown(self, *args, **kwargs):
        if self.__tracer_provider is not None:
            try:
                self.flush()
            finally:
                self.__tracer_provider.shutdown()
