from datetime import datetime

from pydantic import BaseModel


class SourceReference(BaseModel):
    title: str
    source: str
    source_url: str
    published_at: datetime
