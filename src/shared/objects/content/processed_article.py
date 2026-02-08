from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from src.shared.objects.content.article_entity import ArticleEntity


class ProcessedArticle(BaseModel):
    source: str
    source_id: str
    source_url: str
    title: str
    raw_content: str
    summary: str
    entities: List[ArticleEntity] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    sentiment: str = "neutral"  # positive, negative, neutral
    published_at: datetime
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    processing_model: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
