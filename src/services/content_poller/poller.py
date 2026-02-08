"""Content Poller - periodically fetches content from configured sources."""
import asyncio
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from src.shared.interfaces.article_store import ArticleStore
from src.shared.interfaces.content_source import ContentSource
from src.shared.interfaces.message_publisher import MessagePublisher
from src.shared.objects.messages.content_message import ContentMessage
from src.services.content_poller.dedup_cache import DeduplicationCache
from src.shared.observability.logs.logger import Logger
from src.shared.observability.traces.spans.span_context_factory import SpanContextFactory
from src.shared.observability.traces.spans.spanner import Spanner


class ContentPoller:
    """Polls content sources and publishes new content to Kafka."""

    def __init__(
        self,
        sources: List[ContentSource],
        content_repository: ArticleStore,
        message_publisher: MessagePublisher,
        content_topic: str = "content-raw",
        poll_interval: int = 300,
        dedup_cache: Optional[DeduplicationCache] = None,
    ):
        self._logger = Logger()
        self._spanner = Spanner()
        self._sources = sources
        self._content_repository = content_repository
        self._message_publisher = message_publisher
        self._content_topic = content_topic
        self._poll_interval = poll_interval
        self._dedup_cache = dedup_cache
        self._running = True
        self._last_poll: datetime = datetime.now(tz=timezone.utc)

    async def run(self):
        self._logger.info("Content poller started")
        while self._running:
            try:
                await self._poll_cycle()
            except Exception as e:
                self._logger.error(f"Poll cycle error: {e}")

            await asyncio.sleep(self._poll_interval)

    async def _poll_cycle(self):
        with SpanContextFactory.internal("content_poller", "poll_cycle"):
            for source in self._sources:
                try:
                    with SpanContextFactory.client("HTTP", source, "content_poller", "fetch_latest"):
                        items = source.fetch_latest(since=self._last_poll)
                    self._logger.info(f"Fetched {len(items)} items from {source.get_source_name()}")

                    for item in items:
                        if self._is_duplicate(item.source, item.source_id):
                            continue

                        telemetry_headers = self._spanner.inject_telemetry_context({})

                        message = ContentMessage(
                            request_id=str(uuid.uuid4()),
                            raw_content=item,
                            telemetry_headers=telemetry_headers,
                        )
                        with SpanContextFactory.producer(self._content_topic):
                            self._message_publisher.publish(
                                self._content_topic, message.model_dump_json()
                            )

                        if self._dedup_cache:
                            self._dedup_cache.mark_seen(item.source, item.source_id)
                except Exception as e:
                    self._logger.error(f"Error polling {source.get_source_name()}: {e}")

            self._last_poll = datetime.now(tz=timezone.utc)

    def _is_duplicate(self, source: str, source_id: str) -> bool:
        """Check dedup cache first (Redis Set, sub-ms), fall back to MongoDB."""
        if self._dedup_cache:
            with SpanContextFactory.client("REDIS", self._dedup_cache, "content_poller", "dedup_check"):
                if self._dedup_cache.exists(source, source_id):
                    return True
        with SpanContextFactory.client("MONGODB", self._content_repository, "content_poller", "article_exists"):
            return self._content_repository.article_exists(source, source_id)

    def stop(self):
        self._running = False
