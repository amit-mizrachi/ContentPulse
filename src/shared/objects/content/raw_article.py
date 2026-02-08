from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class RawArticle(BaseModel):
    source: str
    source_id: str
    source_url: str
    title: str
    content: str
    published_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
