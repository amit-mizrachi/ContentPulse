ARG BASE_IMAGE=simple-sport-news-base:latest
FROM ${BASE_IMAGE}

EXPOSE 8004

CMD ["python", "-m", "src.services.query_engine.server"]
