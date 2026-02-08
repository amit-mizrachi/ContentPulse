"""Content Poller - periodically fetches content from configured sources."""
import asyncio
import uuid
from datetime import datetime, timezone
from typing import List

from src.interfaces.content_repository import ContentRepository
from src.interfaces.content_source import ContentSource
from src.interfaces.message_publisher import MessagePublisher
from src.objects.messages.content_message import ContentMessage
from src.utils.observability.logs.logger import Logger


class ContentPoller:
    """Polls content sources and publishes new content to Kafka."""

    def __init__(
        self,
        sources: List[ContentSource],
        content_repository: ContentRepository,
        message_publisher: MessagePublisher,
        content_topic: str = "content-raw",
        poll_interval: int = 300,
    ):
        self._logger = Logger()
        self._sources = sources
        self._content_repository = content_repository
        self._message_publisher = message_publisher
        self._content_topic = content_topic
        self._poll_interval = poll_interval
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
        for source in self._sources:
            try:
                items = source.fetch_latest(since=self._last_poll)
                self._logger.info(f"Fetched {len(items)} items from {source.get_source_name()}")

                for item in items:
                    if self._content_repository.article_exists(item.source, item.source_id):
                        continue

                    message = ContentMessage(
                        request_id=str(uuid.uuid4()),
                        raw_content=item,
                    )
                    self._message_publisher.publish(
                        self._content_topic, message.model_dump_json()
                    )
            except Exception as e:
                self._logger.error(f"Error polling {source.get_source_name()}: {e}")

        self._last_poll = datetime.now(tz=timezone.utc)

    def stop(self):
        self._running = False
