"""RSS content source using feedparser."""
from datetime import datetime, timezone
from typing import List, Optional
from hashlib import sha256

import feedparser

from src.shared.interfaces.content_source import ContentSource
from src.shared.objects.content.raw_article import RawArticle


class RSSContentSource(ContentSource):
    def __init__(self, source_name: str, feed_urls: List[str]):
        self._source_name = source_name
        self._feed_urls = feed_urls

    def fetch_latest(self, since: Optional[datetime] = None) -> List[RawArticle]:
        results: List[RawArticle] = []

        for feed_url in self._feed_urls:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries:
                    published = self._parse_date(entry)
                    if since and published <= since:
                        continue

                    source_id = sha256(
                        entry.get("link", entry.get("id", entry.title)).encode()
                    ).hexdigest()[:16]

                    content = entry.get("summary", "") or entry.get("description", "")
                    results.append(RawArticle(
                        source=self._source_name,
                        source_id=source_id,
                        source_url=entry.get("link", ""),
                        title=entry.get("title", ""),
                        content=content,
                        published_at=published,
                        metadata={
                            "feed_url": feed_url,
                            "author": entry.get("author", ""),
                        }
                    ))
            except Exception:
                continue

        return results

    def get_source_name(self) -> str:
        return self._source_name

    @staticmethod
    def _parse_date(entry) -> datetime:
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            from time import mktime
            return datetime.fromtimestamp(mktime(entry.published_parsed), tz=timezone.utc)
        if hasattr(entry, "updated_parsed") and entry.updated_parsed:
            from time import mktime
            return datetime.fromtimestamp(mktime(entry.updated_parsed), tz=timezone.utc)
        return datetime.now(tz=timezone.utc)
