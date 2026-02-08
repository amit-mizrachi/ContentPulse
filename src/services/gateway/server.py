import uvicorn
from fastapi import FastAPI, HTTPException

from src.services.gateway.request_submission_service import RequestSubmissionService
from src.objects.requests.gateway_request import GatewayRequest
from src.utils.observability.logs.logger import Logger
from src.utils.queue.messaging_factory import get_message_publisher
from src.utils.services.aws.appconfig_service import get_config_service
from src.utils.services.clients.redis_client import get_state_repository
from src.utils.services.config.ports import get_service_port

app = FastAPI(title="Gateway Service")
logger = Logger()

SERVICE_PORT_KEY = "services.gateway.port"


def create_request_service() -> RequestSubmissionService:
    config_service = get_config_service()
    return RequestSubmissionService(
        state_repository=get_state_repository(),
        message_publisher=get_message_publisher(),
        inference_topic=config_service.get("topics.inference", "inference"),
    )


request_service = create_request_service()


@app.post("/submit")
async def submit_request(gateway_request: GatewayRequest):
    logger.info("Submitting request")
    response = request_service.submit_request(gateway_request)
    logger.info(f"Successfully submitted request {response.request_id}")
    return response


@app.get("/metadata/{request_id}")
async def get_request_metadata(request_id: str):
    logger.info(f"Getting request metadata for {request_id}")
    try:
        response = request_service.get_request_metadata(request_id)
        logger.info(f"Successfully got metadata for {request_id}")
        return response
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    port = get_service_port(SERVICE_PORT_KEY)
    logger.info(f"Starting Gateway Service on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
