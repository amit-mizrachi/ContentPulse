"""Query Engine Orchestrator - interprets queries, retrieves articles, synthesizes answers."""
import json
import time
from datetime import datetime, timezone

from src.shared.interfaces.repositories.article_repository import ArticleRepository
from src.shared.interfaces.inference.inference_provider import InferenceProvider
from src.shared.interfaces.messaging.message_handler import MessageHandler
from src.shared.objects.inference.inference_config import InferenceConfig
from src.shared.interfaces.repositories.request_state_repository import RequestStateRepository
from src.shared.objects.enums.request_stage import RequestStage
from src.shared.objects.messages.query_message import QueryMessage
from src.shared.objects.results.query_result import QueryResult
from src.shared.objects.results.source_reference import SourceReference
from src.shared.observability.logs.logger import Logger
from src.shared.observability.traces.spans.span_context_factory import SpanContextFactory

INTENT_PROMPT = """Parse this sports query and return a JSON object with:
- "entities": Array of normalized entity strings to search (e.g. ["manchester_united", "cristiano_ronaldo"])
- "categories": Array of category strings (e.g. ["transfer", "injury", "match_result"])
- "entity_type": If the query asks for a specific type of entity, set this to "player"|"team"|"league"|"sport"|"venue", otherwise null
- "date_context": "recent" | "today" | "this_week" | "this_month" | null
- "search_terms": A text search query string for full-text search

Examples:
- "Show me all NBA teams" -> {{"entities": ["nba"], "entity_type": "team", ...}}
- "What players are in the Premier League?" -> {{"entities": ["premier_league"], "entity_type": "player", ...}}
- "Latest Manchester United news" -> {{"entities": ["manchester_united"], "entity_type": null, ...}}

Query: {query}

Return ONLY valid JSON, no markdown."""

SYNTHESIS_PROMPT = """Based on the following sports articles, answer the user's question.
Be concise, factual, and cite your sources by mentioning the article titles.

User question: {query}

Articles:
{articles}

Provide a clear, well-structured answer."""


class QueryEngineOrchestrator(MessageHandler):
    """Orchestrates query processing: intent parsing → article retrieval → answer synthesis."""

    def __init__(
        self,
        state_repository: RequestStateRepository,
        content_repository: ArticleRepository,
        llm_provider: InferenceProvider,
        model: str,
    ):
        self._logger = Logger()
        self._state_repository = state_repository
        self._content_repository = content_repository
        self._llm_provider = llm_provider
        self._model = model

    def handle(self, raw_message, *args, **kwargs) -> bool:
        with SpanContextFactory.internal("query_engine", "orchestrate"):
            query_message = QueryMessage.model_validate(raw_message)
            return self._orchestrate_query(query_message)

    def _orchestrate_query(self, message: QueryMessage) -> bool:
        request_id = message.request_id
        start_time = time.time()

        try:
            self._update_stage(request_id, RequestStage.QueryProcessing)

            # Step 1: Parse intent
            intent = self._parse_intent(message.query_request.query)

            # Step 2: Retrieve articles
            articles = self._retrieve_articles(intent, message)

            # Step 3: Synthesize answer
            answer = self._synthesize_answer(message.query_request.query, articles)

            # Build source references
            sources = [
                SourceReference(
                    title=a.get("title", ""),
                    source=a.get("source", ""),
                    source_url=a.get("source_url", ""),
                    published_at=a.get("published_at", datetime.now(tz=timezone.utc).isoformat()),
                )
                for a in articles[:5]
            ]

            latency_ms = (time.time() - start_time) * 1000
            query_result = QueryResult(
                answer=answer,
                sources=sources,
                metadata={"intent": intent},
                model=self._model,
                latency_ms=latency_ms,
            )

            with SpanContextFactory.client("REDIS", self._state_repository, "query_engine", "save_result"):
                self._state_repository.update(request_id, {
                    "query_result": query_result.model_dump(mode="json"),
                    "stage": RequestStage.Completed.value,
                })

            self._logger.info(f"Query {request_id} completed in {latency_ms:.0f}ms")
            return True

        except Exception as e:
            self._handle_failure(request_id, e)
            return False

    def _parse_intent(self, query: str) -> dict:
        with SpanContextFactory.client("LLM", self._llm_provider, "query_engine", "parse_intent"):
            prompt = INTENT_PROMPT.format(query=query)
            config = InferenceConfig(model=self._model, temperature=0.2)
            output = self._llm_provider.run_inference(prompt=prompt, config=config)
            return json.loads(output.response)

    def _retrieve_articles(self, intent: dict, message: QueryMessage) -> list:
        with SpanContextFactory.client("MONGODB", self._content_repository, "query_engine", "retrieve_articles"):
            articles = []

            # Try structured query first
            entities = intent.get("entities", [])
            categories = intent.get("categories", [])
            entity_type = intent.get("entity_type")

            filters = message.query_request.filters
            sources = filters.sources if filters and filters.sources else None
            date_from = filters.date_from.isoformat() if filters and filters.date_from else None
            date_to = filters.date_to.isoformat() if filters and filters.date_to else None

            if entities or categories or entity_type:
                articles = self._content_repository.query_articles(
                    entities=entities or None,
                    categories=categories or None,
                    sources=sources,
                    date_from=date_from,
                    date_to=date_to,
                    entity_type=entity_type,
                    limit=20,
                )

            # Fall back to text search if no structured results
            if not articles:
                search_terms = intent.get("search_terms", message.query_request.query)
                articles = self._content_repository.search_articles(search_terms, limit=20)

            return articles

    def _synthesize_answer(self, query: str, articles: list) -> str:
        with SpanContextFactory.client("LLM", self._llm_provider, "query_engine", "synthesize_answer"):
            if not articles:
                return "I couldn't find any relevant articles to answer your question."

            articles_text = "\n\n".join(
                f"Title: {a.get('title', 'N/A')}\nSource: {a.get('source', 'N/A')}\nSummary: {a.get('summary', a.get('raw_content', '')[:500])}"
                for a in articles[:10]
            )

            prompt = SYNTHESIS_PROMPT.format(query=query, articles=articles_text)
            config = InferenceConfig(model=self._model, temperature=0.5)
            output = self._llm_provider.run_inference(prompt=prompt, config=config)
            return output.response

    def _update_stage(self, request_id: str, stage: RequestStage):
        with SpanContextFactory.client("REDIS", self._state_repository, "query_engine", "update_stage"):
            self._state_repository.update(request_id, {"stage": stage.value})

    def _handle_failure(self, request_id: str, error: Exception):
        self._logger.error(f"Query failed for {request_id}: {error}")
        with SpanContextFactory.client("REDIS", self._state_repository, "query_engine", "update_failure"):
            self._state_repository.update(request_id, {
                "stage": RequestStage.Failed.value,
                "error_message": str(error),
            })
