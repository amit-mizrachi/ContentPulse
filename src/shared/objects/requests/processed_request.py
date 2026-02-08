from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from src.shared.objects.requests.query_request import QueryRequest
from src.shared.objects.enums.request_stage import RequestStage
from src.shared.objects.results.query_result import QueryResult


class ProcessedQuery(BaseModel):
    """Data structure representing the state of a query through the pipeline."""
    request_id: str
    query_request: QueryRequest
    stage: RequestStage
    query_result: Optional[QueryResult] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
