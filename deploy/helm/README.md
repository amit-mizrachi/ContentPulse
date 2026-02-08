# LLM Judge - Helm Deployment Guide

## Helm Chart Structure

```
helm/
├── charts/
│   └── llm-judge-service/          # Generic chart for all services
│       ├── Chart.yaml
│       ├── values.yaml             # Default values
│       └── templates/
│           ├── _helpers.tpl
│           ├── deployment.yaml
│           ├── service.yaml
│           ├── serviceaccount.yaml
│           ├── hpa.yaml
│           └── ingress.yaml
└── releases/
    ├── gateway-values.yaml         # Gateway service overrides
    ├── inference-values.yaml       # Inference service overrides
    ├── judge-values.yaml           # Judge service overrides
    ├── redis-service-values.yaml   # Redis service overrides
    └── persistence-values.yaml     # Persistence service overrides
```

## Prerequisites

1. **EKS cluster deployed** via Terragrunt
2. **kubectl configured** to access the cluster
3. **Helm 3.x installed**
4. **Docker images pushed** to ECR

## Pre-Deployment Steps

### 1. Get Terraform Outputs

After deploying Terraform/Terragrunt infrastructure, collect the following outputs:

```bash
cd iac/terragrunt/dev

# Get AppConfig IDs
cd appconfig && terragrunt output -json

# Get IAM role ARNs
cd iam-roles && terragrunt output -json service_account_annotations

# Get cluster name
cd eks && terragrunt output eks_cluster.name
```

### 2. Update Values Files

Update each `releases/*-values.yaml` file with:
- **ECR repository URLs** (replace `ACCOUNT_ID`)
- **IRSA role ARNs** (from iam-roles output)
- **AppConfig IDs** (from appconfig output)

### 3. Build and Push Docker Images

```bash
# Authenticate to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Create ECR repositories
for service in gateway-service inference-service judge-service redis-service persistence-service; do
  aws ecr create-repository --repository-name llm-judge/$service --region us-east-1
done

# Build and push images
cd /path/to/LLM_Judge

# Gateway service
docker build -t ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/llm-judge/gateway-service:latest -f ingress_gateway_service/Dockerfile .
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/llm-judge/gateway-service:latest

# Inference service
docker build -t ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/llm-judge/inference-service:latest -f external_inference_service/Dockerfile .
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/llm-judge/inference-service:latest

# Judge service
docker build -t ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/llm-judge/judge-service:latest -f judge_service/Dockerfile .
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/llm-judge/judge-service:latest

# Redis service
docker build -t ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/llm-judge/redis-service:latest -f redis_service/Dockerfile .
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/llm-judge/redis-service:latest

# Persistence service
docker build -t ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/llm-judge/persistence-service:latest -f persistence_service/Dockerfile .
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/llm-judge/persistence-service:latest
```

## Deployment Order

Deploy services in dependency order:

### 1. Redis Service (No dependencies)
```bash
helm install redis-service ./charts/llm-judge-service \
  --namespace llm-judge \
  --create-namespace \
  --values ./releases/redis-service-values.yaml
```

### 2. Persistence Service (No dependencies)
```bash
helm install persistence-service ./charts/llm-judge-service \
  --namespace llm-judge \
  --values ./releases/persistence-values.yaml
```

### 3. Gateway Service (Depends on: redis-service)
```bash
helm install gateway-service ./charts/llm-judge-service \
  --namespace llm-judge \
  --values ./releases/gateway-values.yaml
```

### 4. Inference Service (Depends on: redis-service)
```bash
helm install inference-service ./charts/llm-judge-service \
  --namespace llm-judge \
  --values ./releases/inference-values.yaml
```

### 5. Judge Service (Depends on: redis-service, persistence-service)
```bash
helm install judge-service ./charts/llm-judge-service \
  --namespace llm-judge \
  --values ./releases/judge-values.yaml
```

## Verification

```bash
# Check all pods are running
kubectl get pods -n llm-judge

# Check services
kubectl get svc -n llm-judge

# Check ingress (for gateway-service)
kubectl get ingress -n llm-judge

# Check HPA
kubectl get hpa -n llm-judge

# View logs
kubectl logs -f deployment/gateway-service -n llm-judge
```

## Access Gateway Service

### Get ALB URL
```bash
kubectl get ingress gateway-service -n llm-judge -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

### Test Health Endpoint
```bash
ALB_URL=$(kubectl get ingress gateway-service -n llm-judge -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
curl http://$ALB_URL/health
```

### Submit Test Request
```bash
# BYOK (Bring Your Own Key) - Users provide their own LLM API keys per-request
# This eliminates platform LLM costs - users pay for their own usage
curl -X POST http://$ALB_URL/submit \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is the capital of France?",
    "target_model": {"name": "ChatGPT"},
    "credentials": {
      "openai_api_key": "sk-your-openai-key",
      "google_api_key": "your-google-api-key"
    },
    "judge_model": {"name": "qwen", "version": "2.5:latest"}
  }'
```

## Updating Deployments

### Update Image Tag
```bash
# Update gateway service to new image version
helm upgrade gateway-service ./charts/llm-judge-service \
  --namespace llm-judge \
  --values ./releases/gateway-values.yaml \
  --set image.tag=v1.0.1
```

### Update Configuration
```bash
# Modify values file, then upgrade
helm upgrade inference-service ./charts/llm-judge-service \
  --namespace llm-judge \
  --values ./releases/inference-values.yaml
```

### Rollback
```bash
# Rollback to previous release
helm rollback gateway-service -n llm-judge
```

## Scaling

### Manual Scaling
```bash
# Scale gateway service to 5 replicas
kubectl scale deployment gateway-service --replicas=5 -n llm-judge
```

### Update HPA Limits
```bash
# Increase max replicas for inference service
helm upgrade inference-service ./charts/llm-judge-service \
  --namespace llm-judge \
  --values ./releases/inference-values.yaml \
  --set autoscaling.maxReplicas=30
```

## Troubleshooting

### Pod Not Starting
```bash
# Check pod events
kubectl describe pod <pod-name> -n llm-judge

# Check logs
kubectl logs <pod-name> -n llm-judge

# Check image pull status
kubectl get events -n llm-judge --sort-by='.lastTimestamp'
```

### IRSA Issues
```bash
# Verify service account annotations
kubectl get sa gateway-service -n llm-judge -o yaml

# Check pod has correct service account
kubectl get pod <pod-name> -n llm-judge -o jsonpath='{.spec.serviceAccountName}'

# Test IAM role from pod
kubectl exec -it <pod-name> -n llm-judge -- env | grep AWS
```

### Service Communication Issues
```bash
# Test connectivity between services
kubectl exec -it <gateway-pod> -n llm-judge -- curl http://redis-service:8001/health

# Check service endpoints
kubectl get endpoints -n llm-judge
```

### Ingress Not Working
```bash
# Check ALB controller logs
kubectl logs -f -n kube-system deployment/aws-load-balancer-controller

# Verify ALB created
aws elbv2 describe-load-balancers --region us-east-1

# Check target groups
aws elbv2 describe-target-groups --region us-east-1
```

## Monitoring

### View Metrics
```bash
# CPU/Memory usage
kubectl top pods -n llm-judge

# HPA status
kubectl get hpa -n llm-judge -w
```

### CloudWatch Container Insights
Access via AWS Console:
- CloudWatch → Container Insights → Performance monitoring
- Filter by cluster: `dev-sandbox-llm-judge-cluster`

## Cleanup

### Delete All Services
```bash
# Uninstall all Helm releases
helm uninstall gateway-service -n llm-judge
helm uninstall inference-service -n llm-judge
helm uninstall judge-service -n llm-judge
helm uninstall redis-service -n llm-judge
helm uninstall persistence-service -n llm-judge

# Delete namespace
kubectl delete namespace llm-judge
```

### Delete Individual Service
```bash
helm uninstall <service-name> -n llm-judge
```

## Best Practices

1. **Use specific image tags** in production (not `latest`)
2. **Set resource requests/limits** based on load testing
3. **Enable Pod Disruption Budgets** for HA
4. **Use secrets for sensitive data** (External Secrets Operator)
5. **Monitor HPA metrics** and adjust thresholds
6. **Test rollback procedures** before production
7. **Use separate namespaces** for dev/staging/prod

## Service Dependencies

```
gateway-service        → redis-service
inference-service      → redis-service → SNS → SQS
judge-service          → redis-service, persistence-service → SNS → SQS
persistence-service    → RDS MySQL
redis-service          → ElastiCache Redis
```

## Resource Requirements Summary

| Service | Min CPU | Min Memory | Max Replicas | Notes |
|---------|---------|------------|--------------|-------|
| gateway | 200m | 256Mi | 10 | External facing |
| inference | 500m | 512Mi | 20 | CPU intensive |
| judge | 500m | 512Mi | 15 | CPU intensive |
| redis-service | 100m | 128Mi | 5 | Lightweight |
| persistence | 200m | 256Mi | 8 | DB connection pooling |

**Total Min Resources:** ~2.5 vCPU, ~2.5 GB RAM (at min replicas)
