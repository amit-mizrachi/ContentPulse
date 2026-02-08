# Redis Deployment Quick Start

## TL;DR - One Command Deployment

```bash
cd /Users/nadavfrank/Desktop/projects/LLM_Judge/deploy/iac/terragrunt/dev/helm-releases
terragrunt apply
```

This will:
1. Deploy Redis to Kubernetes (along with all other Helm releases)
2. Create PVC with gp3 storage
3. Configure health probes and resource limits
4. Make Redis available at `redis.llm-judge.svc.cluster.local:6379`

## Step-by-Step Deployment

### 1. Deploy EKS and K8s Config (if not already deployed)
```bash
# Deploy EKS cluster
cd /Users/nadavfrank/Desktop/projects/LLM_Judge/deploy/iac/terragrunt/dev/eks
terragrunt apply

# Deploy gp3 StorageClass (part of k8s-config)
cd /Users/nadavfrank/Desktop/projects/LLM_Judge/deploy/iac/terragrunt/dev/k8s-config
terragrunt apply
```

### 2. Deploy Redis via Helm Releases
```bash
cd /Users/nadavfrank/Desktop/projects/LLM_Judge/deploy/iac/terragrunt/dev/helm-releases
terragrunt apply
```

### 3. Validate Deployment
```bash
# Check pod status
kubectl get pods -n llm-judge -l app=redis

# Check PVC
kubectl get pvc -n llm-judge

# Test connection
kubectl port-forward -n llm-judge svc/redis 6379:6379 &
redis-cli ping

# Clean up port forward
killall kubectl
```

### 4. Update AppConfig (if needed)
```bash
cd /Users/nadavfrank/Desktop/projects/LLM_Judge/deploy/iac/terragrunt/dev/appconfig
terragrunt apply
```

### 5. Restart Services
```bash
kubectl rollout restart deployment -n llm-judge gateway-service
kubectl rollout restart deployment -n llm-judge redis-service
kubectl rollout restart deployment -n llm-judge persistence-service
kubectl rollout restart deployment -n llm-judge inference-service
kubectl rollout restart deployment -n llm-judge judge-service
```

### 6. Verify Migration
```bash
# Check all services are healthy
kubectl get pods -n llm-judge

# Check redis-service can connect to Redis
kubectl logs -n llm-judge -l app=redis-service --tail=50
```

## Quick Tests

### Test Redis Directly
```bash
# Port forward
kubectl port-forward -n llm-judge svc/redis 6379:6379 &

# Test with redis-cli
redis-cli ping
redis-cli set mykey "Hello from K8s"
redis-cli get mykey

# Clean up
killall kubectl
```

### Test from Inside Cluster
```bash
kubectl run -it --rm redis-test --image=redis:7.1-alpine --restart=Never -n llm-judge -- \
  redis-cli -h redis.llm-judge.svc.cluster.local ping
```

## Troubleshooting

### Pod not starting?
```bash
kubectl describe pod -n llm-judge -l app=redis
kubectl logs -n llm-judge -l app=redis
```

### PVC not binding?
```bash
kubectl get pvc -n llm-judge
kubectl describe pvc redis-data -n llm-judge
```

### Services can't connect?
```bash
# Test DNS
kubectl exec -n llm-judge deploy/redis-service -- \
  nslookup redis.llm-judge.svc.cluster.local

# Test connectivity
kubectl exec -n llm-judge deploy/redis-service -- \
  nc -zv redis 6379
```

## Files Reference

- **Chart**: `/deploy/helm/charts/redis/`
- **Values**: `/deploy/helm/releases/redis-values.yaml`
- **Migration Guide**: `/deploy/helm/charts/redis/MIGRATION.md`
- **Full Docs**: `/deploy/helm/charts/redis/README.md`
- **Summary**: `/REDIS_MIGRATION_SUMMARY.md`

## What Changed?

### Before (ElastiCache)
```
redis-service → ElastiCache (AWS) → $35/month
```

### After (Kubernetes)
```
redis-service → redis (Pod) → PVC (gp3) → $1/month
```

**Savings: $34/month (97%)**

## Next Steps

After successful deployment:
1. Monitor for 24-48 hours
2. Validate all services work correctly
3. Decommission ElastiCache: `cd deploy/iac/terragrunt/dev/elasticache && terragrunt destroy`

## Rollback

If you need to rollback, see `/deploy/helm/charts/redis/MIGRATION.md` for detailed steps.
