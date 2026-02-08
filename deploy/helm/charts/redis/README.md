# Redis Helm Chart

Kubernetes-native Redis deployment for LLM Judge microservices.

## Features

- **Persistent storage** with gp3 EBS volumes
- **Dual persistence**: RDB snapshots + AOF
- **Security hardened**: Non-root, no capabilities, readonly root FS
- **Health probes**: Liveness and readiness checks
- **Resource limits**: CPU and memory constraints
- **Anti-affinity**: Avoid single points of failure

## Deployment

Redis is deployed automatically via Terraform Helm provider as part of the infrastructure stack.

```bash
# Deploy via Terragrunt (from deploy/iac/terragrunt/dev/helm-releases)
cd deploy/iac/terragrunt/dev/helm-releases
terragrunt apply

# Verify deployment
kubectl get all,pvc -n llm-judge -l app=redis

# Test connection
kubectl port-forward -n llm-judge svc/redis 6379:6379
redis-cli ping
```

### Manual Deployment (Development Only)

For local testing, you can deploy manually:

```bash
# Install Redis
helm install redis ./charts/redis \
  -f releases/redis-values.yaml \
  -n llm-judge --create-namespace

# Verify
kubectl get all,pvc -n llm-judge -l app=redis
```

## Configuration

### Image
```yaml
image:
  repository: redis
  tag: "7.1-alpine"
  pullPolicy: IfNotPresent
```

### Service
```yaml
service:
  type: ClusterIP
  port: 6379
```

### Resources
```yaml
resources:
  requests:
    cpu: 100m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

### Persistence
```yaml
persistence:
  enabled: true
  storageClassName: "gp3"
  accessMode: ReadWriteOnce
  size: 10Gi
```

### Redis Configuration
```yaml
config:
  maxmemory: "256mb"
  maxmemoryPolicy: "allkeys-lru"
  save: "900 1 300 10 60 10000"
  appendonly: "yes"
  appendfsync: "everysec"
```

## Service Discovery

Redis is accessible at:
- **Service Name**: `redis`
- **FQDN**: `redis.llm-judge.svc.cluster.local`
- **Port**: `6379`

Example connection string:
```
redis://redis.llm-judge.svc.cluster.local:6379
```

## Storage

Uses AWS EBS gp3 volumes via CSI driver:
- **Type**: gp3 (3000 IOPS, 125 MB/s)
- **Size**: 10Gi
- **Encrypted**: Yes
- **Binding**: WaitForFirstConsumer
- **Reclaim**: Delete

## Persistence Strategy

### RDB Snapshots
- Every 900 seconds if 1+ keys changed
- Every 300 seconds if 10+ keys changed
- Every 60 seconds if 10000+ keys changed

### AOF (Append-Only File)
- Enabled with `everysec` fsync
- Auto-rewrite at 100% growth and 64MB min size

## Security

### Pod Security
- Runs as user `999` (redis)
- Non-root enforced
- All capabilities dropped
- Root filesystem readable (Redis needs write to /data)

### Network Security
- ClusterIP service (not exposed externally)
- Accessible only via NetworkPolicy from redis-service pods

## Monitoring

### Health Checks
```bash
# Check pod status
kubectl get pod -n llm-judge -l app=redis

# Check logs
kubectl logs -n llm-judge -l app=redis

# Check Redis info
kubectl exec -n llm-judge deploy/redis -- redis-cli INFO
```

### Performance
```bash
# Memory usage
kubectl exec -n llm-judge deploy/redis -- redis-cli INFO memory

# Stats
kubectl exec -n llm-judge deploy/redis -- redis-cli INFO stats

# Slow queries
kubectl exec -n llm-judge deploy/redis -- redis-cli SLOWLOG GET 10
```

### Persistence
```bash
# Check persistence status
kubectl exec -n llm-judge deploy/redis -- redis-cli INFO persistence

# Check data directory
kubectl exec -n llm-judge deploy/redis -- df -h /data

# Force save
kubectl exec -n llm-judge deploy/redis -- redis-cli SAVE
```

## Troubleshooting

### Pod not starting
```bash
kubectl describe pod -n llm-judge -l app=redis
kubectl get events -n llm-judge --sort-by='.lastTimestamp'
```

### PVC not binding
```bash
kubectl get pvc -n llm-judge
kubectl describe pvc redis-data -n llm-judge
kubectl get storageclass gp3
```

### Connection issues
```bash
# Test from another pod
kubectl run -it --rm debug --image=redis:7.1-alpine --restart=Never -- \
  redis-cli -h redis.llm-judge.svc.cluster.local ping
```

## Backup and Restore

### Manual Backup
```bash
# Force RDB snapshot
kubectl exec -n llm-judge deploy/redis -- redis-cli SAVE

# Copy RDB file
kubectl cp llm-judge/redis-xxxxx:/data/dump.rdb ./backup-$(date +%Y%m%d).rdb
```

### Restore from Backup
```bash
# Scale down Redis
kubectl scale deployment redis -n llm-judge --replicas=0

# Copy backup to PVC
kubectl cp ./backup-20260205.rdb llm-judge/redis-xxxxx:/data/dump.rdb

# Scale up
kubectl scale deployment redis -n llm-judge --replicas=1
```

## Upgrade

```bash
# Update values in releases/redis-values.yaml
vim deploy/helm/releases/redis-values.yaml

# Apply changes via Terragrunt
cd deploy/iac/terragrunt/dev/helm-releases
terragrunt apply

# Verify
kubectl rollout status deployment redis -n llm-judge
```

### Manual Upgrade (Development Only)

```bash
# Upgrade chart manually
helm upgrade redis ./charts/redis \
  -f releases/redis-values.yaml \
  -n llm-judge

# Verify
kubectl rollout status deployment redis -n llm-judge
```

## Uninstall

```bash
# Uninstall via Terragrunt (destroys entire helm-releases module)
cd deploy/iac/terragrunt/dev/helm-releases
terragrunt destroy

# Or manually uninstall just Redis
helm uninstall redis -n llm-judge

# Delete PVC (if needed)
kubectl delete pvc redis-data -n llm-judge
```

## Cost Comparison

| Component | ElastiCache | Kubernetes |
|-----------|-------------|------------|
| Compute | cache.t4g.medium: $30/mo | Shared nodes: $0 |
| Storage | Included | gp3 10GB: $1/mo |
| Backups | $5/mo | Manual/Velero: $0 |
| **Total** | **$35/mo** | **$1/mo** |

**Savings**: ~$34/month (97% reduction)

## References

- [Redis Official Documentation](https://redis.io/docs/)
- [Redis Configuration](https://redis.io/docs/management/config/)
- [Kubernetes StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)
- [AWS EBS CSI Driver](https://github.com/kubernetes-sigs/aws-ebs-csi-driver)
