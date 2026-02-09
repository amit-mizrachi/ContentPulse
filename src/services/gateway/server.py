"""Gateway Service - REST API for request submission and status retrieval."""
import uvicorn
from fastapi import FastAPI, HTTPException, Request

from src.services.gateway.request_submission_service import RequestSubmissionService
from src.shared.objects.requests.query_request import QueryRequest
from src.shared.observability.logs.logger import Logger
from src.shared.observability.traces.spans.span_context_factory import SpanContextFactory
from src.shared.observability.traces.spans.spanner import Spanner
from src.shared.messaging.messaging_factory import get_message_publisher
from src.shared.appconfig_client import get_config_service
from src.shared.repositories.redis_state_repository import get_state_repository

app = FastAPI(title="simple_sport_news Gateway")
logger = Logger()
spanner = Spanner()


def create_request_service() -> RequestSubmissionService:
    config_service = get_config_service()
    return RequestSubmissionService(
        state_repository=get_state_repository(),
        message_publisher=get_message_publisher(),
        query_topic=config_service.get("topics.query", "query"),
    )


request_service = create_request_service()


@app.post("/query")
async def submit_request(query_request: QueryRequest, request: Request):
    telemetry_context = spanner.extract_telemetry_context(dict(request.headers))
    with SpanContextFactory.server("POST", "/query", telemetry_context=telemetry_context):
        logger.info("Submitting request")
        response = request_service.submit_request(query_request)
        logger.info(f"Successfully submitted request {response.request_id}")
        return response


@app.get("/query/{request_id}")
async def get_request_status(request_id: str, request: Request):
    telemetry_context = spanner.extract_telemetry_context(dict(request.headers))
    with SpanContextFactory.server("GET", "/query/{request_id}", telemetry_context=telemetry_context):
        logger.info(f"Getting request status for {request_id}")
        try:
            result = request_service.get_request_status(request_id)
            logger.info(f"Successfully got status for {request_id}")
            return result
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    port = int(get_config_service().get("services.gateway.port"))
    logger.info(f"Starting Gateway Service on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
