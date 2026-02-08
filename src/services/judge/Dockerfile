FROM llm-judge-base:latest

COPY services/judge/ ./services/judge/

# SERVICE_PORT is set at runtime via environment variable
# Default ports are centralized in Terragrunt configuration.hcl

EXPOSE 8004

CMD ["python", "-m", "services.judge.server"]
