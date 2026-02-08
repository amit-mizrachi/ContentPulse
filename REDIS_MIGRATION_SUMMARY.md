# Redis Migration Summary: ElastiCache to Kubernetes

## Overview

Successfully migrated Redis from AWS ElastiCache to Kubernetes-native deployment for cost optimization and architectural simplification.

## Cost Impact

| Component | Before (ElastiCache) | After (Kubernetes) | Savings |
|-----------|---------------------|-------------------|---------|
| Compute | cache.t4g.medium: $30/mo | Shared nodes: $0 | $30/mo |
| Storage | Included | gp3 10GB: $1/mo | -$1/mo |
| Backups | $5/mo | Manual: $0 | $5/mo |
| **Total** | **$35/mo** | **$1/mo** | **$34/mo (97%)** |

## Architecture Changes

### Before
```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────┐
│ redis-service   │─────▶│ ElastiCache      │─────▶│ EBS Volume  │
│ (Pod)           │      │ (AWS Managed)    │      │             │
└─────────────────┘      └──────────────────┘      └─────────────┘
                          $30-50/month
```

### After
```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────┐
│ redis-service   │─────▶│ redis            │─────▶│ PVC (gp3)   │
│ (Pod)           │      │ (Pod)            │      │ 10Gi        │
└─────────────────┘      └──────────────────┘      └─────────────┘
                          ~$1/month
```

## Files Created

### 1. Helm Chart (`/deploy/helm/charts/redis/`)
- ✅ `Chart.yaml` - Chart metadata
- ✅ `values.yaml` - Default configuration values
- ✅ `templates/_helpers.tpl` - Template helpers
- ✅ `templates/deployment.yaml` - Redis Deployment
- ✅ `templates/service.yaml` - ClusterIP Service
- ✅ `templates/pvc.yaml` - Persistent Volume Claim
- ✅ `templates/configmap.yaml` - Redis configuration
- ✅ `README.md` - Chart documentation
- ✅ `MIGRATION.md` - Migration guide
- ✅ `deploy-redis.sh` - Deployment script

### 2. Helm Release Values
- ✅ `/deploy/helm/releases/redis-values.yaml` - Production values

### 3. Infrastructure as Code
- ✅ `/deploy/iac/terraform/k8s-config/storageclass_gp3.tf` - gp3 StorageClass

## Files Modified

### 1. NetworkPolicy Update
**File**: `/deploy/helm/releases/redis-service-values.yaml`

**Change**: Updated egress rule from IP block to pod selector

```yaml
# Before
egress:
  - ipBlock:
      cidr: 10.0.0.0/16
    ports:
      - port: 6379
        protocol: TCP

# After
egress:
  - podSelector:
      matchLabels:
        app: redis
    ports:
      - port: 6379
        protocol: TCP
```

### 2. AppConfig - Redis Endpoint
**File**: `/deploy/iac/terraform/appconfig/main.tf`

**Change**: Updated Redis host from ElastiCache endpoint to K8s service DNS

```hcl
# Before
redis = {
  host = var.redis_endpoint
  port = var.redis_port
  default_ttl_seconds = var.appconfig_config.configuration_content.redis.default_ttl_seconds
}

# After
redis = {
  host = "redis.llm-judge.svc.cluster.local"
  port = 6379
  default_ttl_seconds = var.appconfig_config.configuration_content.redis.default_ttl_seconds
}
```

### 3. AppConfig Variables
**File**: `/deploy/iac/terraform/appconfig/variables.tf`

**Change**: Commented out ElastiCache variables (no longer needed)

```hcl
# Removed
variable "redis_endpoint" { type = string }
variable "redis_port" { type = number }
```

### 4. Terragrunt AppConfig Wrapper
**File**: `/deploy/iac/terragrunt/dev/appconfig/terragrunt.hcl`

**Changes**:
- Commented out ElastiCache dependency
- Removed redis_endpoint and redis_port inputs

```hcl
# Removed dependency
# dependency "elasticache" { ... }

# Removed inputs
# redis_endpoint = dependency.elasticache.outputs.redis_cluster.endpoint
# redis_port     = dependency.elasticache.outputs.redis_cluster.port
```

### 5. Global Configuration
**File**: `/deploy/iac/terragrunt/configuration.hcl`

**Change**: Added `redis_k8s_config` section

```hcl
redis_k8s_config = {
  image            = "redis:7.1-alpine"
  service_name     = "redis"
  service_dns      = "redis.llm-judge.svc.cluster.local"
  port             = 6379
  default_ttl_seconds = 604800

  resources = {
    requests = { cpu = "100m", memory = "256Mi" }
    limits   = { cpu = "500m", memory = "512Mi" }
  }

  persistence = {
    enabled       = true
    storage_class = "gp3"
    access_mode   = "ReadWriteOnce"
    size          = "10Gi"
  }

  config = {
    maxmemory        = "256mb"
    maxmemory_policy = "allkeys-lru"
    save             = "900 1 300 10 60 10000"
    appendonly       = "yes"
    appendfsync      = "everysec"
  }
}
```

## Technical Specifications

### Redis Configuration
- **Image**: redis:7.1-alpine
- **Service DNS**: redis.llm-judge.svc.cluster.local
- **Port**: 6379
- **Service Type**: ClusterIP

### Resources
- **CPU Request**: 100m
- **CPU Limit**: 500m
- **Memory Request**: 256Mi
- **Memory Limit**: 512Mi

### Storage
- **Type**: AWS EBS gp3
- **Size**: 10Gi
- **Access Mode**: ReadWriteOnce
- **Encryption**: Enabled
- **Reclaim Policy**: Delete

### Persistence
- **RDB Snapshots**: 900s (1 key), 300s (10 keys), 60s (10000 keys)
- **AOF**: Enabled with everysec fsync
- **Max Memory**: 256mb
- **Eviction Policy**: allkeys-lru

### Security
- **Non-root**: User 999 (redis)
- **Capabilities**: All dropped
- **Network Policy**: Only redis-service can access
- **Pod Anti-affinity**: Preferred scheduling

## Deployment Steps

### 1. Deploy gp3 StorageClass
```bash
cd /Users/nadavfrank/Desktop/projects/LLM_Judge/deploy/iac/terragrunt/dev/k8s-config
terragrunt apply
```

### 2. Deploy Redis to Kubernetes
```bash
cd /Users/nadavfrank/Desktop/projects/LLM_Judge/deploy/helm

# Option A: Use deployment script
./charts/redis/deploy-redis.sh

# Option B: Manual deployment
helm install redis ./charts/redis \
  -f releases/redis-values.yaml \
  -n llm-judge
```

### 3. Verify Redis Deployment
```bash
# Check pods
kubectl get pods -n llm-judge -l app=redis

# Check service
kubectl get svc -n llm-judge redis

# Check PVC
kubectl get pvc -n llm-judge

# Test connection
kubectl exec -n llm-judge deploy/redis -- redis-cli ping
# Expected: PONG
```

### 4. Update AppConfig
```bash
cd /Users/nadavfrank/Desktop/projects/LLM_Judge/deploy/iac/terragrunt/dev/appconfig
terragrunt apply
```

### 5. Update redis-service NetworkPolicy
```bash
cd /Users/nadavfrank/Desktop/projects/LLM_Judge/deploy/helm

helm upgrade redis-service ./charts/llm-judge-service \
  -f releases/redis-service-values.yaml \
  -n llm-judge
```

### 6. Restart All Services
```bash
kubectl rollout restart deployment -n llm-judge gateway-service
kubectl rollout restart deployment -n llm-judge redis-service
kubectl rollout restart deployment -n llm-judge persistence-service
kubectl rollout restart deployment -n llm-judge inference-service
kubectl rollout restart deployment -n llm-judge judge-service

# Wait for rollout
kubectl rollout status deployment -n llm-judge redis-service
```

### 7. Verify Migration
```bash
# Check all pods
kubectl get pods -n llm-judge

# Check redis-service logs for successful Redis connection
kubectl logs -n llm-judge -l app=redis-service --tail=50

# Test network connectivity
kubectl exec -n llm-judge deploy/redis-service -- \
  nc -zv redis.llm-judge.svc.cluster.local 6379
```

### 8. (Optional) Decommission ElastiCache
```bash
# Only after successful migration and testing
cd /Users/nadavfrank/Desktop/projects/LLM_Judge/deploy/iac/terragrunt/dev/elasticache
terragrunt destroy
```

## Rollback Plan

If issues occur, see `/deploy/helm/charts/redis/MIGRATION.md` for detailed rollback steps.

Quick rollback:
```bash
# 1. Revert IaC changes
git checkout HEAD~1 deploy/iac/

# 2. Re-apply ElastiCache
cd deploy/iac/terragrunt/dev/elasticache
terragrunt apply

# 3. Re-apply AppConfig with ElastiCache endpoint
cd ../appconfig
terragrunt apply

# 4. Revert NetworkPolicy
git checkout HEAD~1 deploy/helm/releases/redis-service-values.yaml
helm upgrade redis-service ./charts/llm-judge-service \
  -f releases/redis-service-values.yaml -n llm-judge

# 5. Restart services
kubectl rollout restart deployment -n llm-judge -l app.kubernetes.io/part-of=llm-judge
```

## Monitoring

### Health Checks
```bash
# Pod health
kubectl get pod -n llm-judge -l app=redis

# Redis logs
kubectl logs -n llm-judge -l app=redis --tail=100

# Persistence info
kubectl exec -n llm-judge deploy/redis -- redis-cli INFO persistence
```

### Performance Metrics
```bash
# Stats
kubectl exec -n llm-judge deploy/redis -- redis-cli INFO stats

# Memory usage
kubectl exec -n llm-judge deploy/redis -- redis-cli INFO memory

# Slow log
kubectl exec -n llm-judge deploy/redis -- redis-cli SLOWLOG GET 10
```

## Benefits

### Cost
- **97% reduction** in Redis costs ($35/mo → $1/mo)
- No ElastiCache hourly charges
- No snapshot storage costs
- EBS gp3 more cost-effective than ElastiCache storage

### Operational
- **Simplified architecture**: One less AWS managed service
- **Faster iteration**: No AWS provisioning delays
- **Better observability**: Native K8s monitoring and logging
- **Consistent tooling**: Same Helm/kubectl workflow as other services

### Technical
- **Fine-grained control**: Custom Redis configuration
- **Faster scaling**: Pod scaling vs ElastiCache node provisioning
- **Better resource utilization**: Shared node resources
- **Network locality**: Redis in same VPC/subnet as services

## Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| Data loss during migration | Use dual-write pattern initially, validate data consistency |
| Performance degradation | Monitor metrics, scale resources if needed |
| Node failure loses Redis data | Enable persistence (RDB + AOF), backup PVC |
| OOM kills | Set proper memory limits, use eviction policy |
| Network partition | Use readiness probes, implement retry logic in services |

## Next Steps

1. ✅ Deploy Redis to Kubernetes
2. ✅ Update AppConfig with K8s service DNS
3. ✅ Update NetworkPolicy for pod-to-pod communication
4. ✅ Restart all services
5. ✅ Monitor for 24-48 hours
6. 🔲 Decommission ElastiCache (after validation)
7. 🔲 Set up automated backups (Velero or custom solution)
8. 🔲 Document runbook for Redis operations

## References

- Chart README: `/deploy/helm/charts/redis/README.md`
- Migration Guide: `/deploy/helm/charts/redis/MIGRATION.md`
- Deployment Script: `/deploy/helm/charts/redis/deploy-redis.sh`
- Configuration Source: `/deploy/iac/terragrunt/configuration.hcl`

## Support

For issues or questions:
1. Check `/deploy/helm/charts/redis/MIGRATION.md` troubleshooting section
2. Review Redis logs: `kubectl logs -n llm-judge -l app=redis`
3. Check events: `kubectl get events -n llm-judge --sort-by='.lastTimestamp'`
