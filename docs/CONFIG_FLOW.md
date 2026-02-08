# Configuration Flow - Single Source of Truth

This document explains how configuration values flow from infrastructure to applications.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SINGLE SOURCE OF TRUTH                                │
│                                                                          │
│    deploy/iac/terragrunt/configuration.hcl                              │
│    ─────────────────────────────────────────                            │
│    - AWS Region (ap-south-1)                                            │
│    - Service Ports (8000-8004)                                          │
│    - Health Check Settings                                              │
│    - SQS Worker Config                                                  │
│    - All other configuration                                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         TERRAFORM APPLY                                  │
│                                                                          │
│    Creates:                                                              │
│    ├── AWS Resources (VPC, EKS, RDS, etc.)                              │
│    ├── AWS AppConfig (runtime config for services)                      │
│    └── Kubernetes ConfigMaps (infra-config, sqs-config)                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌─────────────────────────────┐    ┌─────────────────────────────────────┐
│   infra-config ConfigMap    │    │      sqs-config ConfigMap           │
│   ─────────────────────────│    │      ─────────────────────────      │
│   AWS_REGION                │    │      SQS_MAX_WORKER_COUNT           │
│   PORT_GATEWAY              │    │      SQS_VISIBILITY_TIMEOUT_SECONDS │
│   PORT_REDIS                │    │      SQS_WAIT_TIME_SECONDS          │
│   PORT_PERSISTENCE          │    │      ...                            │
│   PORT_INFERENCE            │    └─────────────────────────────────────┘
│   PORT_JUDGE                │
│   HEALTH_CHECK_*            │
│   ECR_*                     │
│   VPC_CIDR                  │
│   ...                       │
└─────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         HELM DEPLOYMENTS                                 │
│                                                                          │
│    Each service deployment:                                              │
│    - Uses envFrom to load infra-config                                  │
│    - Uses envFrom to load sqs-config (worker services)                  │
│    - Gets SERVICE_PORT from ConfigMap key (e.g., PORT_GATEWAY)          │
│    - Has Reloader annotation for auto-restart on ConfigMap change       │
└─────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       RUNNING PODS                                       │
│                                                                          │
│    Environment Variables:                                               │
│    - SERVICE_PORT=8000 (from ConfigMap)                                 │
│    - AWS_REGION=ap-south-1 (from ConfigMap)                             │
│    - All infra-config values as env vars                                │
│    - All sqs-config values as env vars (if sqsWorker: true)             │
│                                                                          │
│    AppConfig Fetching:                                                   │
│    - Services fetch runtime config (endpoints, secrets) from AppConfig  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Changing Configuration

### To change a port number:

1. Edit `deploy/iac/terragrunt/configuration.hcl`:
   ```hcl
   service_ports = {
     gateway = 8000  # Change this value
     ...
   }
   ```

2. Run Terraform:
   ```bash
   cd deploy/iac/terragrunt/<module>
   terragrunt apply
   ```

3. ConfigMap updates automatically

4. Reloader restarts pods automatically

### To change AWS region:

1. Edit `deploy/iac/terragrunt/configuration.hcl`:
   ```hcl
   aws_region = "eu-west-1"  # Change this
   ```

2. Run Terraform to update ConfigMap

3. Pods restart with new region

## Deployment Order

1. **Terraform/Terragrunt** - Creates infrastructure and ConfigMaps
   ```bash
   cd deploy/iac/terragrunt
   terragrunt run-all apply
   ```

2. **Install Reloader** - Enables auto-restart on ConfigMap changes
   ```bash
   helm repo add stakater https://stakater.github.io/stakater-charts
   helm install reloader stakater/reloader -n kube-system -f deploy/helm/system/reloader-values.yaml
   ```

3. **Deploy Services** - Services read from ConfigMaps
   ```bash
   helm install gateway ./deploy/helm/charts/llm-judge-service -f deploy/helm/releases/gateway-values.yaml -n llm-judge
   helm install redis ./deploy/helm/charts/llm-judge-service -f deploy/helm/releases/redis-service-values.yaml -n llm-judge
   # ... etc
   ```

## ConfigMap Keys Reference

### infra-config

| Key | Example Value | Description |
|-----|---------------|-------------|
| AWS_REGION | ap-south-1 | AWS region |
| AWS_ACCOUNT_ID | 640056739274 | AWS account ID |
| PORT_GATEWAY | 8000 | Gateway service port |
| PORT_REDIS | 8001 | Redis service port |
| PORT_PERSISTENCE | 8002 | Persistence service port |
| PORT_INFERENCE | 8003 | Inference service port |
| PORT_JUDGE | 8004 | Judge service port |
| PORT_REDIS_CACHE | 6379 | ElastiCache Redis port |
| PORT_MYSQL | 3306 | RDS MySQL port |
| HEALTH_CHECK_INTERVAL | 10 | Health check interval (seconds) |
| HEALTH_CHECK_TIMEOUT | 5 | Health check timeout (seconds) |
| HEALTH_CHECK_PATH | /health | Health check endpoint |
| ECR_REPOSITORY_PREFIX | 640056739274.dkr.ecr.ap-south-1.amazonaws.com | ECR prefix |
| ECR_IMAGE_TAG | v1.0.0 | Default image tag |

### sqs-config

| Key | Example Value | Description |
|-----|---------------|-------------|
| SQS_MAX_WORKER_COUNT | 10 | Max concurrent workers |
| SQS_VISIBILITY_TIMEOUT_SECONDS | 300 | Message visibility timeout |
| SQS_WAIT_TIME_SECONDS | 20 | Long polling wait time |

## Docker Compose (Local Development)

For local development, docker-compose uses `.env` file instead of ConfigMaps:

```bash
cp .env.example .env
# Edit .env with your values
docker-compose -f docker/docker-compose.yml up
```

The `.env.example` file contains the same values as the ConfigMaps for consistency.
