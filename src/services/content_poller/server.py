"""Content Poller Service - background polling with health server."""
import asyncio
import signal

from src.services.content_poller.dedup_cache import DeduplicationCache
from src.services.content_poller.poller import ContentPoller
from src.services.content_poller.sources.reddit_content_source import RedditContentSource
from src.services.content_poller.sources.rss_content_source import RSSContentSource
from src.shared.observability.logs.logger import Logger
from src.shared.observability.traces.tracer import Tracer
from src.shared.messaging.messaging_factory import get_message_publisher
from src.shared.aws.appconfig_service import get_config_service
from src.shared.storage.mongodb_article_repository import get_content_repository
from src.shared.config.health import start_health_server_background
from src.shared.config.ports import get_service_port

logger = Logger()
tracer = Tracer()

SERVICE_PORT_KEY = "services.content_poller.port"
DEFAULT_PORT = 8005


def create_content_poller() -> ContentPoller:
    config = get_config_service()

    sources = []

    try:
        reddit_client_id = config.get("reddit.client_id", "")
        reddit_client_secret = config.get("reddit.client_secret", "")
        reddit_user_agent = config.get("reddit.user_agent", "simple_sport_news/1.0")
        subreddits_raw = config.get("reddit.subreddits", "soccer,nba,nfl,formula1")
        subreddits = [s.strip() for s in subreddits_raw.split(",")]

        if reddit_client_id and reddit_client_secret:
            sources.append(RedditContentSource(
                client_id=reddit_client_id,
                client_secret=reddit_client_secret,
                user_agent=reddit_user_agent,
                subreddits=subreddits,
            ))
    except Exception as e:
        logger.warning(f"Reddit source not configured: {e}")

    rss_feeds = {
        "espn": config.get("rss.espn_feeds", "").split(","),
        "bbc_sport": config.get("rss.bbc_feeds", "").split(","),
        "the_athletic": config.get("rss.athletic_feeds", "").split(","),
    }
    for source_name, feeds in rss_feeds.items():
        valid_feeds = [f.strip() for f in feeds if f.strip()]
        if valid_feeds:
            sources.append(RSSContentSource(source_name=source_name, feed_urls=valid_feeds))

    content_topic = config.get("topics.content_raw", "content-raw")
    poll_interval = int(config.get("poller.interval_seconds", 300))

    try:
        dedup_cache = DeduplicationCache()
    except Exception as e:
        logger.warning(f"Dedup cache not available, falling back to MongoDB-only: {e}")
        dedup_cache = None

    return ContentPoller(
        sources=sources,
        content_repository=get_content_repository(),
        message_publisher=get_message_publisher(),
        content_topic=content_topic,
        poll_interval=poll_interval,
        dedup_cache=dedup_cache,
    )


async def main():
    logger.info("Starting Content Poller Service")

    poller = create_content_poller()

    port = get_service_port(SERVICE_PORT_KEY, default=DEFAULT_PORT)
    logger.info(f"Starting health server on port {port}")
    health_task = start_health_server_background(
        service_name="Content Poller Service",
        appconfig_key=SERVICE_PORT_KEY,
        default_port=DEFAULT_PORT
    )

    loop = asyncio.get_running_loop()

    def signal_handler():
        logger.info("Received shutdown signal")
        tracer.shutdown()
        logger.flush()
        poller.stop()
        health_task.cancel()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    await poller.run()


if __name__ == "__main__":
    asyncio.run(main())
