from typing import Optional, List

import uvicorn
from fastapi import FastAPI, HTTPException, Query

from src.objects.requests.history_request import HistoryCreateRequest
from src.objects.responses.history_response import HistoryResponse
from src.services.persistence.database_provider import DatabaseProvider
from src.utils.services.config.ports import get_service_port

app = FastAPI(title="Persistence Service")
database_provider = DatabaseProvider()

SERVICE_PORT_KEY = "services.persistence.port"
DEFAULT_PORT = 8002


@app.post("/history", response_model=HistoryResponse)
async def create_history(request: HistoryCreateRequest):
    history_data = request.model_dump(exclude_none=True)
    with database_provider.history_repository() as history_repo:
        history = history_repo.create(history_data)
        return HistoryResponse.from_orm(history)


@app.get("/history", response_model=List[HistoryResponse])
async def get_history(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None)
):
    with database_provider.history_repository() as history_repo:
        filters = {"status": status} if status else None
        histories = history_repo.get_all(
            limit=limit,
            offset=offset,
            filters=filters,
            order_by="created_at",
            descending=True
        )
        return [HistoryResponse.from_orm(h) for h in histories]


@app.get("/history/{request_id}", response_model=HistoryResponse)
async def get_history_by_request_id(request_id: str):
    with database_provider.history_repository() as history_repo:
        history = history_repo.get_by_request_id(request_id)
        if history is None:
            raise HTTPException(status_code=404, detail="History not found")
        return HistoryResponse.from_orm(history)


@app.get("/health")
async def health_check():
    healthy = database_provider.is_healthy()
    if not healthy:
        raise HTTPException(status_code=503, detail="Database connection failed")
    return {"status": "healthy"}


if __name__ == "__main__":
    port = get_service_port(SERVICE_PORT_KEY, default=DEFAULT_PORT)
    uvicorn.run(app, host="0.0.0.0", port=port)
