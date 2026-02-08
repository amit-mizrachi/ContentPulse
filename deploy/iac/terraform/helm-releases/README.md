# Helm Releases Terraform Module

This Terraform module manages Helm chart deployments for the LLM Judge application on Amazon EKS. It deploys both system components and application services using the Terraform Helm provider.

## Architecture

```
configuration.hcl (single source of truth)
    ↓
terragrunt/dev/helm-releases/terragrunt.hcl
    ↓
terraform/helm-releases/ (uses Helm provider)
    ↓
Deploys to EKS cluster
```

## Module Structure

```
terraform/helm-releases/
├── versions.tf          # Terraform and provider version constraints
├── providers.tf         # Helm and Kubernetes provider configuration
├── variables.tf         # Input variable definitions
├── main.tf             # Helm release resources (system + apps)
├── namespace.tf        # Kubernetes namespace creation
├── configmap.tf        # Infrastructure configuration ConfigMap
├── secretstore.tf      # External Secrets ClusterSecretStore
├── outputs.tf          # Module outputs
└── README.md           # This file
```

## System Components Deployed

The module deploys the following system components to the EKS cluster:

### 1. Metrics Server
- **Namespace**: `kube-system`
- **Purpose**: Provides cluster-wide resource metrics for HPA and kubectl top
- **Chart**: `metrics-server/metrics-server` (v3.12.0)
- **Resources**: 2 replicas, 100m CPU / 128Mi memory requests

### 2. AWS Load Balancer Controller
- **Namespace**: `kube-system`
- **Purpose**: Manages AWS ALB/NLB for Kubernetes ingress
- **Chart**: `eks/aws-load-balancer-controller` (v1.7.1)
- **IRSA**: Uses `aws_load_balancer_controller` IAM role
- **Permissions**: EC2, ELB, WAF, Shield, ACM

### 3. External Secrets Operator
- **Namespace**: `external-secrets-system` (created by module)
- **Purpose**: Syncs secrets from AWS Secrets Manager to Kubernetes secrets
- **Chart**: `external-secrets/external-secrets` (v0.9.11)
- **IRSA**: Uses `external_secrets_operator` IAM role
- **Permissions**: Secrets Manager GetSecretValue, DescribeSecret

### 4. Cluster Autoscaler
- **Namespace**: `kube-system`
- **Purpose**: Automatically adjusts EKS node group sizes based on demand
- **Chart**: `autoscaler/cluster-autoscaler` (v9.34.1)
- **IRSA**: Uses `cluster_autoscaler` IAM role
- **Permissions**: AutoScaling, EC2, EKS

## Application Services Deployed

All application services are deployed to the `llm-judge` namespace using a local Helm chart (`../../../helm/charts/llm-judge-service`):

### 1. Gateway Service
- **Port**: 8000
- **Purpose**: API gateway for request submission
- **IRSA**: SNS Publish permissions (inference topic)
- **Autoscaling**: 2-10 replicas
- **Resources**: 200m-500m CPU, 256Mi-512Mi memory

### 2. Redis Service
- **Port**: 8001
- **Purpose**: Caching service wrapper
- **IRSA**: AppConfig access
- **Autoscaling**: 2-5 replicas
- **Resources**: 200m-500m CPU, 256Mi-512Mi memory

### 3. Persistence Service
- **Port**: 8002
- **Purpose**: Database operations
- **IRSA**: Secrets Manager (RDS credentials), AppConfig
- **Autoscaling**: 2-8 replicas
- **Resources**: 200m-500m CPU, 256Mi-512Mi memory
- **Secrets**: Accesses RDS credentials via ExternalSecret

### 4. Inference Service
- **Port**: 8003
- **Purpose**: LLM inference processing
- **IRSA**: SQS (inference queue), SNS (judge topic)
- **Autoscaling**: 2-20 replicas
- **Resources**: 500m-2000m CPU, 1Gi-2Gi memory

### 5. Judge Service
- **Port**: 8004
- **Purpose**: LLM judging/evaluation
- **IRSA**: SQS (judge queue)
- **Autoscaling**: 2-15 replicas
- **Resources**: 500m-2000m CPU, 1Gi-2Gi memory

## Infrastructure Resources Created

### Namespace
- **Name**: `llm-judge`
- **Labels**: Norman standard tags

### ConfigMap
- **Name**: `infra-config`
- **Namespace**: `llm-judge`
- **Contents**:
  - AWS region and account ID
  - Service endpoints (gateway, redis, persistence, inference, judge)
  - Infrastructure endpoints (Redis cache, RDS)
  - SQS queue URLs (inference, judge)
  - SNS topic ARNs (inference, judge)
  - AppConfig IDs (application, environment, profile)
  - Environment and namespace

### ClusterSecretStore
- **Name**: `aws-secrets-manager`
- **Type**: `external-secrets.io/v1beta1`
- **Purpose**: Configures External Secrets to access AWS Secrets Manager
- **Authentication**: IRSA (JWT) via external-secrets service account

## Dependencies

This module depends on the following Terragrunt modules (all must be deployed first):

1. **eks** - Provides cluster endpoint, CA cert, OIDC provider
2. **iam-roles** - Provides IRSA role ARNs for all services
3. **secrets** - Provides RDS credentials secret name/ARN
4. **appconfig** - Provides AppConfig application/environment/profile IDs
5. **rds** - Provides RDS endpoint/port
6. **sqs** - Provides SQS queue URLs
7. **sns** - Provides SNS topic ARNs

> **Note:** Redis runs in-cluster (deployed by this module) instead of ElastiCache for cost savings.

## Input Variables

### Core Variables
- `aws_region` - AWS region
- `aws_account_id` - AWS account ID
- `environment` - Environment (dev/staging/prod)
- `project_name` - Project name

### EKS Configuration
- `cluster_name` - EKS cluster name
- `cluster_endpoint` - EKS cluster endpoint URL
- `cluster_ca_certificate` - EKS cluster CA cert (base64 encoded)
- `cluster_oidc_provider_arn` - EKS OIDC provider ARN

### IAM Roles (IRSA)
- `iam_role_arns` - Map of service name to IAM role ARN

### Secrets
- `secrets_config` - Secrets Manager configuration (RDS credentials)

### AppConfig
- `appconfig_ids` - AppConfig resource IDs

### ECR
- `ecr_repository_prefix` - ECR repository prefix
- `image_tag` - Docker image tag (default: v1.0.0)

### Services
- `service_names` - Map of service names
- `service_ports` - Map of service ports
- `infrastructure_endpoints` - Redis cache and RDS endpoints
- `sqs_queue_urls` - SQS queue URLs
- `sns_topic_arns` - SNS topic ARNs
- `autoscaling` - Autoscaling configuration

### Kubernetes
- `namespace` - Kubernetes namespace (default: llm-judge)

## Outputs

### Namespace
- `namespace.name` - Application namespace name
- `namespace.uid` - Namespace UID

### System Releases
- `system_releases.metrics_server` - Metrics Server release info
- `system_releases.aws_load_balancer_controller` - ALB Controller release info
- `system_releases.external_secrets` - External Secrets release info
- `system_releases.cluster_autoscaler` - Cluster Autoscaler release info

### Application Releases
- `application_releases.gateway_service` - Gateway service release info
- `application_releases.redis_service` - Redis service release info
- `application_releases.persistence_service` - Persistence service release info
- `application_releases.inference_service` - Inference service release info
- `application_releases.judge_service` - Judge service release info

### Infrastructure
- `configmap_name` - Infrastructure ConfigMap name
- `secret_store_name` - ClusterSecretStore name

## Usage

### Deploy via Terragrunt

```bash
# Navigate to the Terragrunt wrapper directory
cd /Users/nadavfrank/Desktop/projects/LLM_Judge/deploy/iac/terragrunt/dev/helm-releases

# Initialize Terraform
terragrunt init

# Plan the deployment
terragrunt plan

# Apply the deployment
terragrunt apply
```

### Deploy all dependencies first

```bash
# Deploy in order (from project root)
cd /Users/nadavfrank/Desktop/projects/LLM_Judge/deploy/iac/terragrunt/dev

# 1. VPC and Security Groups
terragrunt run-all apply --terragrunt-include-dir vpc --terragrunt-include-dir security-groups

# 2. EKS
terragrunt run-all apply --terragrunt-include-dir eks

# 3. Data layer (Redis runs in-cluster, no ElastiCache needed)
terragrunt run-all apply --terragrunt-include-dir rds

# 4. Messaging
terragrunt run-all apply --terragrunt-include-dir sns --terragrunt-include-dir sqs

# 5. Secrets and AppConfig
terragrunt run-all apply --terragrunt-include-dir secrets --terragrunt-include-dir appconfig

# 6. IAM Roles
terragrunt run-all apply --terragrunt-include-dir iam-roles

# 7. Helm Releases (this module)
terragrunt run-all apply --terragrunt-include-dir helm-releases
```

## Provider Configuration

The module configures both Helm and Kubernetes providers to authenticate with the EKS cluster using AWS CLI:

```hcl
provider "helm" {
  kubernetes {
    host                   = var.cluster_endpoint
    cluster_ca_certificate = base64decode(var.cluster_ca_certificate)
    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args        = ["eks", "get-token", "--cluster-name", var.cluster_name, "--region", var.aws_region]
    }
  }
}
```

**Requirements**:
- AWS CLI installed and configured
- Sufficient IAM permissions to access the EKS cluster
- `aws eks update-kubeconfig` run at least once

## Deployment Order

The module enforces deployment order using Terraform `depends_on`:

1. **Namespace** - Created first
2. **ConfigMap** - Created with namespace
3. **System Components** - Deployed in parallel (metrics-server, alb-controller, external-secrets, cluster-autoscaler)
4. **ClusterSecretStore** - Created after external-secrets
5. **Application Services** - Deployed after system components and infrastructure ConfigMap

## Chart Path Resolution

Application services use a local Helm chart:
```hcl
local_chart_path = "${path.module}/../../../helm/charts/llm-judge-service"
```

This resolves to:
```
/Users/nadavfrank/Desktop/projects/LLM_Judge/deploy/helm/charts/llm-judge-service
```

The chart is shared across all application services, with values customized per service.

## Norman IAC Patterns

This module follows Norman IAC patterns:

- ✅ **Separate module folder** for resource type (helm-releases)
- ✅ **variables.tf + outputs.tf** required
- ✅ **Separate files** for distinct resources (namespace.tf, configmap.tf, secretstore.tf)
- ✅ **Meaningful resource identifiers** (e.g., `llm_judge_namespace`, `infra_config`)
- ✅ **Norman tags** on all resources
- ✅ **Configuration centralized** in configuration.hcl
- ✅ **No hardcoded values** - everything from variables

## Troubleshooting

### Helm release fails to deploy
1. Check EKS cluster is accessible: `kubectl get nodes`
2. Verify AWS credentials: `aws sts get-caller-identity`
3. Check Helm provider logs in Terraform output

### Service account IRSA not working
1. Verify IAM role exists: `aws iam get-role --role-name <role-name>`
2. Check OIDC provider is configured on EKS cluster
3. Verify role ARN is correctly annotated on service account

### External Secrets not syncing
1. Check ClusterSecretStore status: `kubectl describe clustersecretstore aws-secrets-manager`
2. Verify external-secrets pod logs: `kubectl logs -n external-secrets-system -l app.kubernetes.io/name=external-secrets`
3. Confirm IRSA role has Secrets Manager permissions

### Application pods not starting
1. Check ConfigMap exists: `kubectl get configmap infra-config -n llm-judge`
2. Verify service account exists with IRSA annotation
3. Check pod logs: `kubectl logs -n llm-judge <pod-name>`

## Future Enhancements

- [ ] Add support for custom Helm chart values per environment
- [ ] Add support for Helm chart versioning
- [ ] Add support for Helm chart repositories
- [ ] Add support for Helm chart dependencies
- [ ] Add monitoring/alerting Helm charts (Prometheus, Grafana)
- [ ] Add logging Helm charts (Fluentd, Elasticsearch, Kibana)

## References

- [Terraform Helm Provider](https://registry.terraform.io/providers/hashicorp/helm/latest/docs)
- [Terraform Kubernetes Provider](https://registry.terraform.io/providers/hashicorp/kubernetes/latest/docs)
- [AWS Load Balancer Controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/)
- [External Secrets Operator](https://external-secrets.io/)
- [Cluster Autoscaler](https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler)
- [Metrics Server](https://github.com/kubernetes-sigs/metrics-server)
