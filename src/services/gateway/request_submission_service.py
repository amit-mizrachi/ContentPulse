"""Request Submission Service - handles request submission and metadata retrieval."""
import uuid

from src.interfaces.message_publisher import MessagePublisher
from src.interfaces.state_repository import StateRepository
from src.objects.enums.request_stage import RequestStage
from src.objects.enums.request_status import RequestStatus
from src.objects.messages.inference_message import InferenceMessage
from src.objects.enums.processed_request import ProcessedRequest
from src.objects.requests.gateway_request import GatewayRequest
from src.objects.responses.gateway_response import GatewayResponse
from src.utils.observability.logs.logger import Logger
from src.utils.services.aws.appconfig_service import get_config_service
from src.utils.queue.messaging_factory import get_message_publisher
from src.utils.services.clients.redis_client import get_state_repository


class RequestSubmissionService:
    """Handles the ingestion of new requests and their metadata retrieval."""

    def __init__(
        self,
        state_repository: StateRepository = None,
        message_publisher: MessagePublisher = None,
        inference_topic: str = None,
    ):
        self._logger = Logger()

        self._state_repository = state_repository or get_state_repository()
        self._message_publisher = message_publisher or get_message_publisher()

        if inference_topic is not None:
            self._inference_topic = inference_topic
        else:
            config_service = get_config_service()
            self._inference_topic = config_service.get("topics.inference", "inference")

    def submit_request(self, gateway_request: GatewayRequest) -> GatewayResponse:
        request_id = self._generate_id()

        processed_request = ProcessedRequest(
            request_id=request_id,
            gateway_request=gateway_request,
            stage=RequestStage.Gateway
        )
        self._state_repository.create(request_id, processed_request.model_dump(mode="json"))

        self._publish_to_inference(request_id, gateway_request)

        return GatewayResponse(
            request_id=request_id,
            status=RequestStatus.Accepted
        )

    def get_request_metadata(self, request_id: str) -> ProcessedRequest:
        state_data = self._state_repository.get(request_id)
        if state_data is None:
            raise KeyError(f"Request {request_id} not found")
        return ProcessedRequest.model_validate(state_data)

    def _publish_to_inference(self, request_id: str, request: GatewayRequest) -> None:
        message = InferenceMessage(
            request_id=request_id,
            gateway_request=request
        )

        self._message_publisher.publish(self._inference_topic, message.model_dump_json())

    @staticmethod
    def _generate_id() -> str:
        return str(uuid.uuid4())
