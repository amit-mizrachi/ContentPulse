from typing import Optional

from pydantic import BaseModel

from src.shared.objects.requests.query_filters import QueryFilters


class QueryRequest(BaseModel):
    query: str
    filters: Optional[QueryFilters] = None
