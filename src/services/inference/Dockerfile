FROM llm-judge-base:latest

COPY services/inference/ ./services/inference/

# SERVICE_PORT is set at runtime via environment variable
# Default ports are centralized in Terragrunt configuration.hcl

EXPOSE 8003

CMD ["python", "-m", "services.inference.server"]
