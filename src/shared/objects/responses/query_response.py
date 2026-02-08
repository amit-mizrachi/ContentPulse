from pydantic import BaseModel

from src.shared.objects.enums.request_status import RequestStatus


class QueryResponse(BaseModel):
    request_id: str
    status: RequestStatus
