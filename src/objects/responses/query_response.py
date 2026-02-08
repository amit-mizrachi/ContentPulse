from pydantic import BaseModel

from src.objects.enums.request_status import RequestStatus


class QueryResponse(BaseModel):
    request_id: str
    status: RequestStatus
