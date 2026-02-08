FROM llm-judge-base:latest

COPY services/gateway/ ./services/gateway/

# SERVICE_PORT is set at runtime via environment variable
# Default ports are centralized in Terragrunt configuration.hcl

EXPOSE 8000

CMD ["python", "-m", "services.gateway.server"]
