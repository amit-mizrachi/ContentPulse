from typing import Optional, List

from sqlalchemy.orm import Session

from src.services.persistence.models.history import RequestHistory
from src.services.persistence.repositories.base_repository import BaseRepository


class RequestHistoryNotFoundError(Exception):
    """Raised when a request history record is not found."""
    def __init__(self, request_id: str):
        self.request_id = request_id
        super().__init__(f"Request history not found for request_id: {request_id}")


class HistoryRepository(BaseRepository[RequestHistory]):
    def __init__(self, session: Session):
        super().__init__(session, RequestHistory)

    def find_by_request_id(self, request_id: str) -> Optional[RequestHistory]:
        return self._session.query(RequestHistory).filter(
            RequestHistory.request_id == request_id
        ).first()

    def get_by_request_id(self, request_id: str) -> RequestHistory:
        result = self.find_by_request_id(request_id)
        if result is None:
            raise RequestHistoryNotFoundError(request_id)
        return result

    def get_by_status(
        self,
        status: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[RequestHistory]:
        return self.get_all(
            limit=limit,
            offset=offset,
            filters={"status": status},
            order_by="created_at",
            descending=True
        )
