"""Gateway Service - REST API for query submission and status retrieval."""
import uvicorn
from fastapi import FastAPI, HTTPException

from src.services.gateway.query_submission_service import QuerySubmissionService
from src.objects.requests.query_request import QueryRequest
from src.utils.observability.logs.logger import Logger
from src.utils.queue.messaging_factory import get_message_publisher
from src.utils.services.aws.appconfig_service import get_config_service
from src.utils.services.clients.redis_client import get_state_repository
from src.utils.services.config.ports import get_service_port

app = FastAPI(title="ContentPulse Gateway")
logger = Logger()

SERVICE_PORT_KEY = "services.gateway.port"


def create_query_service() -> QuerySubmissionService:
    config_service = get_config_service()
    return QuerySubmissionService(
        state_repository=get_state_repository(),
        message_publisher=get_message_publisher(),
        query_topic=config_service.get("topics.query", "query"),
    )


query_service = create_query_service()


@app.post("/query")
async def submit_query(query_request: QueryRequest):
    logger.info("Submitting query")
    response = query_service.submit_query(query_request)
    logger.info(f"Successfully submitted query {response.request_id}")
    return response


@app.get("/query/{request_id}")
async def get_query_status(request_id: str):
    logger.info(f"Getting query status for {request_id}")
    try:
        result = query_service.get_query_status(request_id)
        logger.info(f"Successfully got status for {request_id}")
        return result
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    port = get_service_port(SERVICE_PORT_KEY)
    logger.info(f"Starting Gateway Service on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
