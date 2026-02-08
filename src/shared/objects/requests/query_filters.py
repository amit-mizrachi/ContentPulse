from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class QueryFilters(BaseModel):
    sources: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
