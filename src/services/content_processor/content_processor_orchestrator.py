"""Content Processor Orchestrator - enriches raw content via LLM and stores in MongoDB."""
import json
import time
from datetime import datetime, timezone

from src.interfaces.content_repository import ContentRepository
from src.interfaces.llm_provider import LLMProvider
from src.interfaces.message_handler import MessageHandler
from src.objects.inference.inference_config import InferenceConfig
from src.objects.content.processed_article import ProcessedArticle, Entity
from src.objects.messages.content_message import ContentMessage
from src.utils.observability.logs.logger import Logger

PROCESSING_PROMPT = """Analyze this sports article and return a JSON object with:
- "summary": A 2-3 sentence summary
- "entities": Array of {{"name": str, "type": "person"|"team"|"league"|"venue", "normalized": str (lowercase, no spaces)}}
- "categories": Array of strings (e.g. "football", "premier_league", "transfer", "injury")
- "sentiment": "positive"|"negative"|"neutral"

Article title: {title}
Article content: {content}

Return ONLY valid JSON, no markdown."""


class ContentProcessorOrchestrator(MessageHandler):
    """Processes raw content: LLM enrichment → MongoDB storage."""

    def __init__(
        self,
        content_repository: ContentRepository,
        llm_provider: LLMProvider,
        model: str,
    ):
        self._logger = Logger()
        self._content_repository = content_repository
        self._llm_provider = llm_provider
        self._model = model

    def handle(self, raw_message, *args, **kwargs) -> bool:
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

            prompt = PROCESSING_PROMPT.format(title=raw.title, content=raw.content[:3000])
            config = InferenceConfig(model=self._model, temperature=0.3)
            output = self._llm_provider.run_inference(prompt=prompt, config=config)

            enrichment = json.loads(output.response)

            entities = [
                Entity(
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

            self._content_repository.store_article(article)

            latency = (time.time() - start_time) * 1000
            self._logger.info(
                f"Processed content {request_id} from {raw.source}/{raw.source_id} in {latency:.0f}ms"
            )
            return True

        except Exception as e:
            self._logger.error(f"Failed to process content {request_id}: {e}")
            return False
