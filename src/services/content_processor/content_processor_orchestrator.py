"""Content Processor Orchestrator - enriches raw content via LLM and stores in MongoDB."""
import json
import time
from datetime import datetime, timezone

from src.shared.interfaces.article_store import ArticleStore
from src.shared.interfaces.llm_provider import LLMProvider
from src.shared.interfaces.message_handler import MessageHandler
from src.shared.objects.inference.inference_config import InferenceConfig
from src.shared.objects.content.article_entity import ArticleEntity
from src.shared.objects.content.processed_article import ProcessedArticle
from src.shared.objects.messages.content_message import ContentMessage
from src.shared.observability.logs.logger import Logger
from src.shared.observability.traces.spans.span_context_factory import SpanContextFactory

PROCESSING_PROMPT = """Analyze this sports article and return a JSON object with:
- "summary": A 2-3 sentence summary
- "entities": Array of extracted entities (see rules below)
- "categories": Array of topic tags (e.g. "transfer", "injury", "match_result", "contract", "retirement")
- "sentiment": "positive"|"negative"|"neutral"

Entity extraction rules:
1. Each entity: {{"name": str, "type": "player"|"team"|"league"|"sport"|"venue", "normalized": str}}
2. "normalized" must be lowercase with underscores, no special characters (e.g. "kylian_mbappe", "premier_league")
3. CRITICAL: Extract BOTH explicit AND implicit entities. Use your world knowledge:
   - If a player is mentioned, also add their current team, league, and sport as separate entities
   - If a team is mentioned, also add their league and sport
   - If a league is mentioned, also add the sport
4. Extract ALL mentioned players, teams, leagues, sports, and venues — not just the main subject

Example: An article mentioning only "LeBron James" should produce:
- {{"name": "LeBron James", "type": "player", "normalized": "lebron_james"}}
- {{"name": "Los Angeles Lakers", "type": "team", "normalized": "los_angeles_lakers"}}
- {{"name": "NBA", "type": "league", "normalized": "nba"}}
- {{"name": "Basketball", "type": "sport", "normalized": "basketball"}}

Article title: {title}
Article content: {content}

Return ONLY valid JSON, no markdown."""


class ContentProcessorOrchestrator(MessageHandler):
    """Processes raw content: LLM enrichment → MongoDB storage."""

    def __init__(
        self,
        content_repository: ArticleStore,
        llm_provider: LLMProvider,
        model: str,
    ):
        self._logger = Logger()
        self._content_repository = content_repository
        self._llm_provider = llm_provider
        self._model = model

    def handle(self, raw_message, *args, **kwargs) -> bool:
        with SpanContextFactory.internal("content_processor", "orchestrate"):
            try:
                content_message = ContentMessage.model_validate(raw_message)
                return self._process_content(content_message)
            except Exception as e:
                self._logger.error(f"Content processing failed: {e}")
                return False

    def _process_content(self, message: ContentMessage) -> bool:
        raw = message.raw_content
        request_id = message.request_id

        try:
            start_time = time.time()

            with SpanContextFactory.client("LLM", self._llm_provider, "content_processor", "run_inference"):
                prompt = PROCESSING_PROMPT.format(title=raw.title, content=raw.content[:3000])
                config = InferenceConfig(model=self._model, temperature=0.3)
                output = self._llm_provider.run_inference(prompt=prompt, config=config)
                enrichment = json.loads(output.response)

            entities = [
                ArticleEntity(
                    name=e.get("name", ""),
                    type=e.get("type", ""),
                    normalized=e.get("normalized", e.get("name", "").lower().replace(" ", "_"))
                )
                for e in enrichment.get("entities", [])
            ]

            article = ProcessedArticle(
                source=raw.source,
                source_id=raw.source_id,
                source_url=raw.source_url,
                title=raw.title,
                raw_content=raw.content,
                summary=enrichment.get("summary", ""),
                entities=entities,
                categories=enrichment.get("categories", []),
                sentiment=enrichment.get("sentiment", "neutral"),
                published_at=raw.published_at,
                ingested_at=datetime.now(tz=timezone.utc),
                processed_at=datetime.now(tz=timezone.utc),
                processing_model=self._model,
                metadata=raw.metadata,
            )

            with SpanContextFactory.client("MONGODB", self._content_repository, "content_processor", "store_article"):
                self._content_repository.store_article(article)

            latency = (time.time() - start_time) * 1000
            self._logger.info(
                f"Processed content {request_id} from {raw.source}/{raw.source_id} in {latency:.0f}ms"
            )
            return True

        except Exception as e:
            self._logger.error(f"Failed to process content {request_id}: {e}")
            return False
