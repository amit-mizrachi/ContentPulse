"""Query Submission Service - handles query submission and status retrieval."""
import uuid

from src.shared.interfaces.message_publisher import MessagePublisher
from src.shared.interfaces.state_repository import StateRepository
from src.shared.objects.enums.request_stage import RequestStage
from src.shared.objects.enums.request_status import RequestStatus
from src.shared.objects.requests.processed_request import ProcessedQuery
from src.shared.objects.messages.query_message import QueryMessage
from src.shared.objects.requests.query_request import QueryRequest
from src.shared.objects.responses.query_response import QueryResponse
from src.shared.observability.logs.logger import Logger
from src.shared.observability.traces.spans.span_context_factory import SpanContextFactory
from src.shared.observability.traces.spans.spanner import Spanner


class QuerySubmissionService:
    """Handles the submission of queries and their status retrieval."""

    def __init__(
        self,
        state_repository: StateRepository,
        message_publisher: MessagePublisher,
        query_topic: str = "query",
    ):
        self._logger = Logger()
        self._spanner = Spanner()
        self._state_repository = state_repository
        self._message_publisher = message_publisher
        self._query_topic = query_topic

    def submit_query(self, query_request: QueryRequest) -> QueryResponse:
        request_id = str(uuid.uuid4())

        processed_query = ProcessedQuery(
            request_id=request_id,
            query_request=query_request,
            stage=RequestStage.Gateway,
        )
        with SpanContextFactory.client("REDIS", self._state_repository, "gateway", "create"):
            self._state_repository.create(request_id, processed_query.model_dump(mode="json"))

        telemetry_headers = self._spanner.inject_telemetry_context({})

        message = QueryMessage(
            request_id=request_id,
            query_request=query_request,
            telemetry_headers=telemetry_headers,
        )
        with SpanContextFactory.producer(self._query_topic):
            self._message_publisher.publish(self._query_topic, message.model_dump_json())

        return QueryResponse(
            request_id=request_id,
            status=RequestStatus.Accepted,
        )

    def get_query_status(self, request_id: str) -> ProcessedQuery:
        with SpanContextFactory.client("REDIS", self._state_repository, "gateway", "get"):
            state_data = self._state_repository.get(request_id)
        if state_data is None:
            raise KeyError(f"Query {request_id} not found")
        return ProcessedQuery.model_validate(state_data)
