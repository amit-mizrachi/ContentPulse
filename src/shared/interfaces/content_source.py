"""Content Source Interface - defines the contract for content ingestion sources."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from src.shared.objects.content.raw_article import RawArticle


class ContentSource(ABC):
    @abstractmethod
    def fetch_latest(self, since: Optional[datetime] = None) -> List[RawArticle]:
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        pass
