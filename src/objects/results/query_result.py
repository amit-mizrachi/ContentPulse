from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class SourceReference(BaseModel):
    title: str
    source: str
    source_url: str
    published_at: datetime


class QueryResult(BaseModel):
    answer: str
    sources: List[SourceReference] = []
    metadata: dict = {}
    model: str = ""
    latency_ms: float = 0.0
