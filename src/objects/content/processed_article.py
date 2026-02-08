from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Entity(BaseModel):
    name: str
    type: str  # person, team, league, venue
    normalized: str


class ProcessedArticle(BaseModel):
    source: str
    source_id: str
    source_url: str
    title: str
    raw_content: str
    summary: str
    entities: List[Entity] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    sentiment: str = "neutral"  # positive, negative, neutral
    published_at: datetime
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    processing_model: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
