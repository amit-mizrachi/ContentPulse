from typing import List

from pydantic import BaseModel

from src.shared.objects.results.source_reference import SourceReference


class QueryResult(BaseModel):
    answer: str
    sources: List[SourceReference] = []
    metadata: dict = {}
    model: str = ""
    latency_ms: float = 0.0
