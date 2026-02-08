import uvicorn
from fastapi import FastAPI, HTTPException

from src.objects.enums.processed_request import ProcessedRequest
from src.services.redis.request_repository import RequestRepository
from src.utils.services.config.ports import get_service_port

app = FastAPI(title="Redis Service")
request_repository = RequestRepository()

SERVICE_PORT_KEY = "services.redis.port"
DEFAULT_PORT = 8001


@app.post("/requests/{request_id}", response_model=ProcessedRequest)
async def create_request(request_id: str, request: ProcessedRequest):
    if request.request_id != request_id:
        raise HTTPException(status_code=400, detail="Request ID mismatch")
    return request_repository.create(request)


@app.get("/requests/{request_id}", response_model=ProcessedRequest)
async def get_request(request_id: str):
    request = request_repository.get(request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Request not found")
    return request


@app.patch("/requests/{request_id}", response_model=ProcessedRequest)
async def update_request(request_id: str, updates: dict):
    request = request_repository.update(request_id, updates)
    if request is None:
        raise HTTPException(status_code=404, detail="Request not found")
    return request


@app.delete("/requests/{request_id}")
async def delete_request(request_id: str):
    deleted = request_repository.delete(request_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Request not found")
    return {"status": "deleted"}


@app.get("/health")
async def health_check():
    healthy = request_repository.is_healthy()
    if not healthy:
        raise HTTPException(status_code=503, detail="Redis connection failed")
    return {"status": "healthy"}


if __name__ == "__main__":
    port = get_service_port(SERVICE_PORT_KEY, default=DEFAULT_PORT)
    uvicorn.run(app, host="0.0.0.0", port=port)
