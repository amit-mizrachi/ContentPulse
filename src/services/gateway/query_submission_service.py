"""Query Submission Service - handles query submission and status retrieval."""
import uuid

from src.interfaces.message_publisher import MessagePublisher
from src.interfaces.state_repository import StateRepository
from src.objects.enums.request_stage import RequestStage
from src.objects.enums.request_status import RequestStatus
from src.objects.enums.processed_request import ProcessedQuery
from src.objects.messages.query_message import QueryMessage
from src.objects.requests.query_request import QueryRequest
from src.objects.responses.query_response import QueryResponse
from src.utils.observability.logs.logger import Logger


class QuerySubmissionService:
    """Handles the submission of queries and their status retrieval."""

    def __init__(
        self,
        state_repository: StateRepository,
        message_publisher: MessagePublisher,
        query_topic: str = "query",
    ):
        self._logger = Logger()
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
        self._state_repository.create(request_id, processed_query.model_dump(mode="json"))

        message = QueryMessage(
            request_id=request_id,
            query_request=query_request,
        )
        self._message_publisher.publish(self._query_topic, message.model_dump_json())

        return QueryResponse(
            request_id=request_id,
            status=RequestStatus.Accepted,
        )

    def get_query_status(self, request_id: str) -> ProcessedQuery:
        state_data = self._state_repository.get(request_id)
        if state_data is None:
            raise KeyError(f"Query {request_id} not found")
        return ProcessedQuery.model_validate(state_data)
