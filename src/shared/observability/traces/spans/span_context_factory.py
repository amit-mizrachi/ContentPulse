import opentelemetry.trace

from src.shared.observability.traces.spans.span_attributes_factory import SpanAttributesFactory
from src.shared.observability.traces.spans.spanner import Spanner


class SpanContextFactory:

    @staticmethod
    def client(target_system, norman_client, target_service, target_method, end_on_exit=True, telemetry_context=None):
        spanner = Spanner()
        
        client_span_attributes = SpanAttributesFactory.client()
        client_span = spanner.start_span(
            name=f"{target_system.upper()}-{target_service}-{target_method}",
            kind=opentelemetry.trace.SpanKind.CLIENT,
            attributes=client_span_attributes,
            telemetry_context=telemetry_context
        )

        return spanner.use_span_context_manager(client_span, end_on_exit=end_on_exit)

    @staticmethod
    def server(request_method: str, request_path: str, telemetry_context=None, end_on_exit=True):
        spanner = Spanner()

        server_span_attributes = SpanAttributesFactory.server()
        server_span = spanner.start_span(
            name=f"HTTP-{request_method}-{request_path}",
            kind=opentelemetry.trace.SpanKind.SERVER,
            attributes=server_span_attributes,
            telemetry_context=telemetry_context
        )

        return spanner.use_span_context_manager(server_span, end_on_exit=end_on_exit)

    @staticmethod
    def producer(topic_name, messaging_system: str = "SNS", telemetry_context=None, end_on_exit=True):
        spanner = Spanner()

        producer_span_attributes = SpanAttributesFactory.producer()
        producer_span = spanner.start_span(
            name=f"{messaging_system.upper()}-{topic_name}",
            kind=opentelemetry.trace.SpanKind.PRODUCER,
            attributes=producer_span_attributes,
            telemetry_context=telemetry_context
        )

        return spanner.use_span_context_manager(producer_span, end_on_exit=end_on_exit)

    @staticmethod
    def consumer(topic_name: str, message_id: str, message_contents: dict, messaging_system: str = "SQS", telemetry_context=None, end_on_exit=True):
        spanner = Spanner()

        consumer_span_attributes = SpanAttributesFactory.consumer()
        consumer_span = spanner.start_span(
            name=f"{messaging_system.upper()}-{topic_name}",
            kind=opentelemetry.trace.SpanKind.CONSUMER,
            attributes=consumer_span_attributes,
            telemetry_context=telemetry_context
        )

        return spanner.use_span_context_manager(consumer_span, end_on_exit=end_on_exit)

    @staticmethod
    def internal(service_name: str, operation: str, telemetry_context=None, end_on_exit=True):
        spanner = Spanner()

        internal_span = spanner.start_span(
            name=f"{service_name}.{operation}",
            kind=opentelemetry.trace.SpanKind.INTERNAL,
            attributes={},
            telemetry_context=telemetry_context
        )

        return spanner.use_span_context_manager(internal_span, end_on_exit=end_on_exit)
