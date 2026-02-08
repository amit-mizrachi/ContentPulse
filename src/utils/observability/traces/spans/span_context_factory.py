import opentelemetry.trace
from starlette.types import Scope

from src.utils.observability.traces.spans.span_attributes_factory import SpanAttributesFactory
from src.utils.observability.traces.spans.spanner import Spanner


class SpanContextFactory:

    @staticmethod
    def client(target_system, norman_client, target_service, target_method, end_on_exit=True, telemetry_context=None):
        spanner = Spanner()
        
        client_span_attributes = SpanAttributesFactory.client(target_system, norman_client, target_service, target_method)
        client_span = spanner.start_span(
            name=f"{target_system.upper()}-{target_service}-{target_method}",
            kind=opentelemetry.trace.SpanKind.CLIENT,
            attributes=client_span_attributes,
            telemetry_context=telemetry_context
        )

        return spanner.use_span_context_manager(client_span, end_on_exit=end_on_exit)

    @staticmethod
    def server(headers: dict, scope: Scope, norman_ids: dict, telemetry_context = None, end_on_exit = True):
        spanner = Spanner()
        
        server_span_attributes = SpanAttributesFactory.server(headers, scope, norman_ids)
        request_method = server_span_attributes["http.request.method"]
        request_path = server_span_attributes["url.path"]

        server_span = spanner.start_span(
            name=f"HTTP-{request_method}-{request_path}",
            kind=opentelemetry.trace.SpanKind.SERVER,
            attributes=server_span_attributes,
            telemetry_context=telemetry_context
        )

        return spanner.use_span_context_manager(server_span ,end_on_exit=end_on_exit)

    @staticmethod
    def producer(topic_name, telemetry_context = None, end_on_exit = True):
        spanner = Spanner()
        
        producer_span_attributes = SpanAttributesFactory.producer(topic_name)
        producer_span = spanner.start_span(
            name=f"SNS-{topic_name}",
            kind=opentelemetry.trace.SpanKind.PRODUCER,
            attributes=producer_span_attributes,
            telemetry_context=telemetry_context
        )

        return spanner.use_span_context_manager(producer_span, end_on_exit=end_on_exit)

    @staticmethod
    def consumer(topic_name: str, message_id: str, message_contents: dict, telemetry_context = None, end_on_exit = True):
        spanner = Spanner()

        consumer_span_attributes = SpanAttributesFactory.consumer(topic_name, message_id, message_contents)
        consumer_span = spanner.start_span(
            name=f"SQS-{topic_name}",
            kind=opentelemetry.trace.SpanKind.CONSUMER,
            attributes=consumer_span_attributes,
            telemetry_context=telemetry_context
        )

        return spanner.use_span_context_manager(consumer_span, end_on_exit=end_on_exit)
