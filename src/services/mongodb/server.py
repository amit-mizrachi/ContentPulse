"""MongoDB Service - REST API for article storage and retrieval."""
import uvicorn
from fastapi import FastAPI, HTTPException, Query

from src.objects.content.processed_article import ProcessedArticle
from src.services.mongodb.article_repository import ArticleRepository
from src.services.mongodb.mongodb_provider import MongoDBProvider
from src.utils.services.config.ports import get_service_port

app = FastAPI(title="MongoDB Service")

provider = MongoDBProvider()
article_repository = ArticleRepository(provider)

SERVICE_PORT_KEY = "services.mongodb.port"
DEFAULT_PORT = 8002


@app.post("/articles")
async def store_article(article: ProcessedArticle):
    result = article_repository.store_article(article)
    return result


@app.get("/articles")
async def query_articles(
    entities: str = Query(None),
    categories: str = Query(None),
    sources: str = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None),
    limit: int = Query(20)
):
    entity_list = entities.split(",") if entities else None
    category_list = categories.split(",") if categories else None
    source_list = sources.split(",") if sources else None

    return article_repository.query_articles(
        entities=entity_list,
        categories=category_list,
        sources=source_list,
        date_from=date_from,
        date_to=date_to,
        limit=limit
    )


@app.get("/articles/search")
async def search_articles(q: str = Query(...), limit: int = Query(20)):
    return article_repository.search_articles(q, limit)


@app.get("/articles/exists")
async def article_exists(source: str = Query(...), source_id: str = Query(...)):
    return {"exists": article_repository.article_exists(source, source_id)}


@app.get("/health")
async def health_check():
    healthy = article_repository.is_healthy()
    if not healthy:
        raise HTTPException(status_code=503, detail="MongoDB connection failed")
    return {"status": "healthy"}


if __name__ == "__main__":
    port = get_service_port(SERVICE_PORT_KEY, default=DEFAULT_PORT)
    uvicorn.run(app, host="0.0.0.0", port=port)
