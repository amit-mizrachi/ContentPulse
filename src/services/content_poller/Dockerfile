ARG BASE_IMAGE=contentpulse-base:latest
FROM ${BASE_IMAGE}

EXPOSE 8005

CMD ["python", "-m", "src.services.content_poller.server"]
