FROM llm-judge-base:latest

COPY services/redis/ ./services/redis/

# SERVICE_PORT is set at runtime via environment variable
# Default ports are centralized in Terragrunt configuration.hcl

EXPOSE 8001

CMD ["python", "-m", "services.redis.server"]
