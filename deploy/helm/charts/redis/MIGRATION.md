# Redis Migration: ElastiCache to Kubernetes

## Overview
Migrated Redis from AWS ElastiCache to Kubernetes-native deployment for:
- **Cost savings**: ~$30-50/month
- **Simplified architecture**: One less AWS managed service
- **Better observability**: Native K8s monitoring
- **Faster iteration**: No AWS provisioning delays

## Architecture

### Before (ElastiCache)
```
redis-service (Pod) --> ElastiCache (AWS) --> EBS volume
                         $30-50/month
```

### After (Kubernetes)
```
redis-service (Pod) --> redis (Pod) --> PVC (gp3 EBS)
                         ~$5/month
```

## Deployment

### 1. Deploy Redis to Kubernetes
```bash
cd /Users/nadavfrank/Desktop/projects/LLM_Judge/deploy/helm

# Install Redis cache
helm install redis ./charts/redis \
  -f releases/redis-values.yaml \
  -n llm-judge

# Verify deployment
kubectl get all,pvc -n llm-judge -l app=redis
kubectl logs -n llm-judge -l app=redis --tail=50
```

### 2. Test Redis Connection
```bash
# Port-forward to Redis
kubectl port-forward -n llm-judge svc/redis 6379:6379

# Test with redis-cli (in another terminal)
redis-cli ping
# Expected: PONG

# Test basic operations
redis-cli set test "hello"
redis-cli get test
# Expected: "hello"
```

### 3. Update AppConfig
```bash
cd /Users/nadavfrank/Desktop/projects/LLM_Judge/deploy/iac/terragrunt/dev/appconfig

# Apply updated AppConfig with K8s Redis DNS
terragrunt apply
```

### 4. Update redis-service NetworkPolicy
```bash
# Upgrade redis-service to use pod selector instead of IP block
helm upgrade redis-service ./charts/llm-judge-service \
  -f releases/redis-service-values.yaml \
  -n llm-judge
```

### 5. Restart Services
```bash
# Restart all services to pick up new Redis endpoint
kubectl rollout restart deployment -n llm-judge gateway-service
kubectl rollout restart deployment -n llm-judge redis-service
kubectl rollout restart deployment -n llm-judge persistence-service
kubectl rollout restart deployment -n llm-judge inference-service
kubectl rollout restart deployment -n llm-judge judge-service

# Watch rollout status
kubectl rollout status deployment -n llm-judge redis-service
```

### 6. Verify Migration
```bash
# Check all services are healthy
kubectl get pods -n llm-judge

# Check redis-service logs
kubectl logs -n llm-judge -l app=redis-service --tail=50

# Verify network connectivity
kubectl exec -n llm-judge deploy/redis-service -- \
  nc -zv redis.llm-judge.svc.cluster.local 6379
```

### 7. Decommission ElastiCache (Optional)
```bash
# Only after successful migration and testing
cd /Users/nadavfrank/Desktop/projects/LLM_Judge/deploy/iac/terragrunt/dev/elasticache
terragrunt destroy
```

## Configuration Details

### Redis Service DNS
- **Service Name**: `redis`
- **Namespace**: `llm-judge`
- **FQDN**: `redis.llm-judge.svc.cluster.local`
- **Port**: `6379`

### Storage
- **StorageClass**: `gp3` (AWS EBS)
- **Size**: `10Gi`
- **Access Mode**: `ReadWriteOnce`
- **Reclaim Policy**: `Delete`

### Resources
- **CPU Request**: `100m`
- **CPU Limit**: `500m`
- **Memory Request**: `256Mi`
- **Memory Limit**: `512Mi`

### Persistence
- **RDB Snapshots**: Every 900s (1), 300s (10), 60s (10000)
- **AOF**: Enabled with `everysec` fsync
- **Max Memory**: `256mb`
- **Eviction Policy**: `allkeys-lru`

### Security
- **Run as non-root**: User `999`
- **No capabilities**: All dropped
- **Network Policy**: Only redis-service can access

## Rollback Plan

If issues occur, rollback to ElastiCache:

```bash
# 1. Re-provision ElastiCache
cd /Users/nadavfrank/Desktop/projects/LLM_Judge/deploy/iac/terragrunt/dev/elasticache
# Uncomment elasticache module in root
terragrunt apply

# 2. Revert AppConfig changes
cd /Users/nadavfrank/Desktop/projects/LLM_Judge/deploy/iac/terragrunt/dev/appconfig
git checkout HEAD~1 terragrunt.hcl
cd /Users/nadavfrank/Desktop/projects/LLM_Judge/deploy/iac/terraform/appconfig
git checkout HEAD~1 main.tf variables.tf
terragrunt apply

# 3. Revert redis-service NetworkPolicy
cd /Users/nadavfrank/Desktop/projects/LLM_Judge/deploy/helm
git checkout HEAD~1 releases/redis-service-values.yaml
helm upgrade redis-service ./charts/llm-judge-service \
  -f releases/redis-service-values.yaml \
  -n llm-judge

# 4. Restart services
kubectl rollout restart deployment -n llm-judge -l app.kubernetes.io/part-of=llm-judge
```

## Monitoring

### Health Checks
```bash
# Check Redis pod health
kubectl get pod -n llm-judge -l app=redis

# Check Redis logs
kubectl logs -n llm-judge -l app=redis --tail=100

# Check persistence
kubectl exec -n llm-judge deploy/redis -- redis-cli INFO persistence
```

### Performance Metrics
```bash
# Redis stats
kubectl exec -n llm-judge deploy/redis -- redis-cli INFO stats

# Memory usage
kubectl exec -n llm-judge deploy/redis -- redis-cli INFO memory

# Check PVC usage
kubectl exec -n llm-judge deploy/redis -- df -h /data
```

## Troubleshooting

### Redis pod not starting
```bash
# Check pod events
kubectl describe pod -n llm-judge -l app=redis

# Check PVC binding
kubectl get pvc -n llm-judge redis-data

# Check StorageClass
kubectl get storageclass gp3
```

### Services can't connect to Redis
```bash
# Verify service DNS resolution
kubectl exec -n llm-judge deploy/redis-service -- \
  nslookup redis.llm-judge.svc.cluster.local

# Check NetworkPolicy
kubectl get networkpolicy -n llm-judge

# Test connectivity
kubectl exec -n llm-judge deploy/redis-service -- \
  nc -zv redis 6379
```

### Data persistence issues
```bash
# Check Redis persistence config
kubectl exec -n llm-judge deploy/redis -- redis-cli CONFIG GET save
kubectl exec -n llm-judge deploy/redis -- redis-cli CONFIG GET appendonly

# Check data directory
kubectl exec -n llm-judge deploy/redis -- ls -la /data

# Force save
kubectl exec -n llm-judge deploy/redis -- redis-cli SAVE
```

## Files Changed

### New Files
1. `deploy/helm/charts/redis/Chart.yaml`
2. `deploy/helm/charts/redis/values.yaml`
3. `deploy/helm/charts/redis/templates/_helpers.tpl`
4. `deploy/helm/charts/redis/templates/deployment.yaml`
5. `deploy/helm/charts/redis/templates/service.yaml`
6. `deploy/helm/charts/redis/templates/pvc.yaml`
7. `deploy/helm/charts/redis/templates/configmap.yaml`
8. `deploy/helm/releases/redis-values.yaml`
9. `deploy/iac/terraform/k8s-config/storageclass_gp3.tf`

### Modified Files
1. `deploy/helm/releases/redis-service-values.yaml` - NetworkPolicy egress
2. `deploy/iac/terraform/appconfig/main.tf` - Redis host to K8s DNS
3. `deploy/iac/terraform/appconfig/variables.tf` - Removed redis vars
4. `deploy/iac/terragrunt/dev/appconfig/terragrunt.hcl` - Removed elasticache dependency
5. `deploy/iac/terragrunt/configuration.hcl` - Added redis_k8s_config

## Cost Impact

### Before (ElastiCache)
- **cache.t4g.medium**: ~$30/month
- **EBS backups**: ~$5/month
- **Total**: ~$35/month

### After (Kubernetes)
- **gp3 10GB**: ~$1/month
- **No additional EC2 cost** (runs on existing nodes)
- **Total**: ~$1/month

**Savings**: ~$34/month (~97% reduction)
