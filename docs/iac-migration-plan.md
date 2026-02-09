# simple_sport_news IaC Migration Plan

## Context

simple_sport_news is a sports content aggregation platform. This plan adapts production-ready Terraform/Terragrunt/Helm infrastructure from the LLM-Judge project, adds a dual-inference architecture with GPU/CPU scheduling, and uses `configuration.hcl` as the single source of truth.

### Key Decisions
- **Fresh `deploy/` directory** inside simple_sport_news (reusable modules copied from LLM-Judge)
- **`configuration.hcl`** drives everything: AppConfig, CI/CD, Helm values, scheduling
- **MongoDB Atlas** (Free tier) instead of RDS MySQL
- **Dual messaging: Kafka (Strimzi) + SNS/SQS** both active
- **Scale-to-zero GPU** via KEDA based on Kafka consumer lag
- **Single Docker image, two Helm releases** for inference (content-processor + query-engine)
- **Inference mode in config** determines node scheduling (CPU vs GPU)

### Messaging Architecture
```
Kafka (Strimzi Operator on K8s):
  - content-processing topic -> content-processor consumer group
  - query-answering topic   -> query-engine consumer group
  - Used for: inter-service messaging (primary)

SNS/SQS (AWS Native):
  - content_processing topic/queue
  - query_answering topic/queue
  - Used for: AWS integrations, fan-out, dead letter queues
```

### Inference Architecture
```
configuration.hcl (SSoT)
  |-- inference.content_processor.mode = "remote" | "local"
  |-- inference.query_engine.mode = "remote"
          |
          v
    Terraform reads config -> sets Helm values
          |
          |-- content-processor -> CPU nodes (remote) OR GPU nodes (local)
          |-- query-engine      -> CPU nodes (always remote)
          |
          v
    KEDA (GPU only): scale pods 0<->N based on Kafka consumer lag
    Cluster Autoscaler: scale GPU nodes 0<->M
```

---

## Phase 1: Project Setup - COMPLETED

Created directory structure and copied as-is modules from LLM-Judge.

### Directory Structure
```
simple_sport_news/deploy/
|-- iac/
|   |-- terraform/
|   |   |-- vpc/              # COPIED as-is
|   |   |-- eks/              # COPIED as-is
|   |   |-- ec2/              # COPIED as-is
|   |   |-- ecr/              # COPIED as-is
|   |   |-- sns/              # COPIED as-is
|   |   |-- sqs/              # COPIED as-is
|   |   |-- security-groups/  # COPIED, deleted ingress-mysql-from-eks.tf
|   |   |-- iam-roles/        # REWRITTEN service roles
|   |   |-- iam-policies/     # COPIED as-is
|   |   |-- secrets/          # REWRITTEN (generic for_each)
|   |   |-- appconfig/        # REWRITTEN (MongoDB, Kafka, new queues/topics)
|   |   |-- helm-releases/    # MAJOR REWRITE (Strimzi, KEDA, NVIDIA, new services)
|   |   |-- k8s-config/       # COPIED as-is
|   |   |-- budgets/          # COPIED as-is
|   |-- terragrunt/
|       |-- configuration.hcl  # COMPLETE REWRITE
|       |-- root.hcl           # COPIED, auto-derives project name
|       |-- dev/               # 12 wrappers (no rds/)
|-- helm/
    |-- charts/
    |   |-- simple-sport-news-service/  # REWRITTEN from llm-judge-service
    |   |-- redis/                 # COPIED as-is
    |-- system/
```

---

## Phase 2: configuration.hcl - COMPLETED

Complete rewrite of the SSoT file. Key blocks:
- **4 services**: gateway (8000), content_poller (8005), content_processor (8003), query_engine (8004)
- **Kafka config**: Strimzi operator, KRaft mode, 1 broker (dev), topics with 3 partitions
- **Inference config**: content_processor + query_engine, both "remote" mode by default
- **MongoDB config**: database_name="simple-sport-news", collections: articles, queries
- **Secrets config**: llm_api_keys, mongodb_credentials, reddit_credentials
- **SNS topics**: content_processing, query_answering
- **SQS queues**: content-processing, query-answering
- **ECR repos**: gateway-service, content-poller-service, inference-service (shared image)

---

## Phase 3: Terraform Module Modifications - COMPLETED

### security-groups/
- Deleted `ingress-mysql-from-eks.tf`
- Removed `rds_security_group` output

### iam-roles/
- Deleted: irsa_redis_service.tf, irsa_persistence_service.tf, irsa_judge_service.tf, irsa_inference_service.tf
- Created: irsa_content_poller_service.tf (SNS publish), irsa_content_processor_service.tf (SQS consume + Secrets Manager), irsa_query_engine_service.tf (SQS consume + Secrets Manager)
- Updated: irsa_gateway_service.tf (namespace: simple-sport-news, SNS topic: query_answering)
- Rewrote: variables.tf, outputs.tf (7 IRSA roles)

### secrets/
- Deleted: rds_credentials.tf
- Created: main.tf (generic `for_each = var.secrets_config`)
- Rewrote: variables.tf (removed rds_credentials var), outputs.tf (dynamic for expression)

### appconfig/
- Renamed: all `llm_judge` resources to `contentpulse`, `inference` to `runtime`
- Removed: MySQL/RDS references
- Updated: SQS/SNS keys to content_processing/query_answering
- Rewrote: variables.tf (removed rds_endpoint/rds_port), outputs.tf

### helm-releases/ (MAJOR REWRITE)
- Deleted: app_inference_service.tf, app_judge_service.tf, app_persistence_service.tf, app_redis_service.tf
- Created:
  - app_content_poller_service.tf - CPU nodes, SNS publisher
  - app_content_processor_service.tf - Conditional GPU/CPU scheduling based on inference_mode
  - app_query_engine_service.tf - Always CPU, shared inference-service image
  - system_strimzi_operator.tf - Strimzi Kafka operator
  - system_keda.tf - KEDA operator (conditional on GPU mode)
  - system_nvidia_device_plugin.tf - NVIDIA plugin (conditional on GPU enabled)
  - infra_kafka_cluster.tf - Strimzi Kafka CRD + KafkaTopic CRDs
- Modified: namespace.tf, helm_commons.tf, configmap.tf, app_gateway_service.tf, variables.tf, outputs.tf

---

## Phase 4: Helm Chart Modifications - COMPLETED

- Renamed Chart.yaml: `simple-sport-news-service`
- Updated _helpers.tpl: all `llm-judge-service` -> `simple-sport-news-service`
- Rewrote deployment.yaml: added `command:`, `args:`, `INFERENCE_MODE` env var
- Updated all templates: hpa, service, serviceaccount, pdb, ingress, networkpolicy, externalsecret
- Rewrote values.yaml: added command, args, keda, inferenceMode sections
- Created: keda-scaledobject.yaml template (Kafka-based GPU autoscaling)

---

## Phase 5: Terragrunt Wrappers - COMPLETED

- root.hcl: auto-derives project_name from configuration.hcl
- 12 dev wrappers created (no rds/):
  - vpc, sns, budgets (no deps)
  - sqs (depends on sns)
  - security-groups, ec2 (depends on vpc)
  - ecr (independent)
  - eks (depends on vpc, security-groups)
  - secrets (independent)
  - appconfig (depends on sns, sqs)
  - iam-roles (depends on eks, sns, sqs, secrets)
  - helm-releases (depends on everything)

---

## Phase 6: Legacy Cleanup - COMPLETED

### Removed dead LLM-Judge services:
- `src/services/judge/` - LLM-Judge specific, broken imports
- `src/services/persistence/` - SQLAlchemy/MySQL, not used
- `src/services/redis/` - HTTP Redis wrapper, not used (direct redis_client.py instead)
- `src/services/inference/` - LLM-Judge inference, broken imports

### Removed dead objects/interfaces:
- `src/objects/judge_models/` - Qwen judge models
- `src/interfaces/judge_gateway.py`
- `src/interfaces/persistence_gateway.py`

### KEPT (explicitly preserved):
- `src/utils/queue/kafka/` - kafka_consumer.py, kafka_producer.py (ACTIVE - used by all services)
- `src/utils/queue/sqs/` - SQS consumer/publisher (ACTIVE)
- `src/utils/queue/messaging_factory.py` - Routes to Kafka or SQS based on config (ACTIVE)
- docker-compose Kafka service (ACTIVE - for local dev)

---

## Phase 7: Verification

### 7.1 Terraform validate (per module)
```bash
for dir in vpc eks ec2 ecr sns sqs security-groups iam-roles secrets appconfig helm-releases k8s-config budgets; do
  cd ~/Desktop/projects/simple_sport_news/deploy/iac/terraform/$dir
  terraform init -backend=false && terraform validate
done
```

### 7.2 Terragrunt plan (dry run)
```bash
cd ~/Desktop/projects/simple_sport_news/deploy/iac/terragrunt/dev
terragrunt run-all plan --terragrunt-non-interactive
```

### 7.3 Helm template validation
```bash
# Test gateway release
helm template test-gw ./deploy/helm/charts/simple-sport-news-service \
  --set service.name=gateway-service --set service.containerPort=8000

# Test content-processor in GPU mode
helm template test-cp ./deploy/helm/charts/simple-sport-news-service \
  --set service.name=content-processor-service \
  --set "command[0]=python" --set "command[1]=-m" \
  --set "command[2]=src.services.content_processor.server" \
  --set keda.enabled=true \
  --set "nodeSelector.nvidia\.com/gpu=true"
```

### 7.4 Local docker-compose smoke test
```bash
cd ~/Desktop/projects/simple_sport_news/docker
docker compose config && docker compose up --build
```

---

## File Manifest Summary

| Action | Count | Key Files |
|--------|-------|-----------|
| **CREATE** | ~25 | configuration.hcl, 3 IRSA roles, 3 Helm app releases, 3 system releases, 1 infra Kafka CRD, KEDA template, root.hcl, 12 terragrunt wrappers |
| **MODIFY** | ~15 | Chart.yaml, values.yaml, deployment.yaml, _helpers.tpl, configmap.tf, namespace.tf, appconfig/, helm_commons.tf, gateway IRSA, variables/outputs |
| **DELETE** | ~12 | 4 IRSA files, 4 Helm release files, ingress-mysql SG, rds_credentials.tf, 4 dead service dirs, 3 dead object/interface files |
| **COPY AS-IS** | ~50+ | vpc/, eks/, ec2/, ecr/, sns/, sqs/, k8s-config/, budgets/, iam-policies/, redis chart |
