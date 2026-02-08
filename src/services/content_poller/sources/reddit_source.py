"""Reddit content source using PRAW."""
from datetime import datetime, timezone
from typing import List, Optional

import praw

from src.shared.interfaces.content_source import ContentSource
from src.shared.objects.content.raw_article import RawArticle


class RedditSource(ContentSource):
    """Polls configured subreddits for sports content."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        user_agent: str,
        subreddits: List[str] = None,
    ):
        self._reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )
        self._subreddits = subreddits or ["soccer", "nba", "nfl", "formula1"]

    def fetch_latest(self, since: Optional[datetime] = None) -> List[RawArticle]:
        results: List[RawArticle] = []
        for sub_name in self._subreddits:
            try:
                subreddit = self._reddit.subreddit(sub_name)
                for submission in subreddit.hot(limit=25):
                    created = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)
                    if since and created <= since:
                        continue

                    content = submission.selftext or submission.url
                    results.append(RawArticle(
                        source="reddit",
                        source_id=submission.id,
                        source_url=f"https://reddit.com{submission.permalink}",
                        title=submission.title,
                        content=content,
                        published_at=created,
                        metadata={
                            "subreddit": sub_name,
                            "score": submission.score,
                            "num_comments": submission.num_comments,
                            "author": str(submission.author),
                        }
                    ))
            except Exception:
                continue

        return results

    def get_source_name(self) -> str:
        return "reddit"
