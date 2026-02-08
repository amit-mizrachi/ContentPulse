FROM llm-judge-base:latest

COPY services/persistence/ ./services/persistence/

# SERVICE_PORT is set at runtime via environment variable
# Default ports are centralized in Terragrunt configuration.hcl

EXPOSE 8002

CMD ["python", "-m", "services.persistence.server"]
