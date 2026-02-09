ARG BASE_IMAGE=simple-sport-news-base:latest
FROM ${BASE_IMAGE}

EXPOSE 8003

CMD ["python", "-m", "src.services.content_processor.server"]
