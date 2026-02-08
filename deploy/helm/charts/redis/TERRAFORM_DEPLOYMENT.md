# Redis Terraform Helm Deployment

## Overview

Redis is now deployed via the Terraform Helm provider as part of the infrastructure-as-code stack. This eliminates the need for manual shell scripts and ensures Redis is deployed in the correct dependency order.

## Architecture

```
Terragrunt (helm-releases)
  → Terraform Helm Provider
    → Redis Helm Chart (local)
      → Deployment
      → Service
      → PVC (gp3 StorageClass)
      → ConfigMap
```

## Dependency Chain

```
1. EKS Cluster (eks module)
2. Kubernetes Namespace (helm-releases module)
3. StorageClass gp3 (helm-releases module)
4. Redis Helm Release (helm-releases module)
5. Application Services (helm-releases module)
```

## Files Modified

### Terraform Module: `deploy/iac/terraform/helm-releases/`

1. **main.tf**
   - Added `redis_chart_path` and `redis_values_file_path` to locals
   - Added `helm_release.redis_cache` resource
   - Depends on: metrics_server, namespace, storageclass

2. **outputs.tf**
   - Added `infrastructure_releases` output block
   - Includes Redis cache release status

3. **storageclass.tf** (NEW)
   - Creates `kubernetes_storage_class.gp3` resource
   - Used by Redis PVC for persistent storage

### Helm Chart: `deploy/helm/charts/redis/`

1. **Deleted Files**
   - `deploy-redis.sh` - No longer needed (replaced by Terraform)
   - `validate-redis.sh` - No longer needed (replaced by Terraform)

2. **Updated Documentation**
   - `README.md` - Updated deployment, upgrade, and uninstall sections
   - `QUICKSTART.md` - Updated to reflect Terraform deployment method
   - `TERRAFORM_DEPLOYMENT.md` (NEW) - This file

## Deployment

### Production Deployment

```bash
cd deploy/iac/terragrunt/dev/helm-releases
terragrunt apply
```

This deploys:
- Kubernetes namespace
- gp3 StorageClass
- Redis cache
- All application services

### Verify Deployment

```bash
# Check Redis pod
kubectl get pods -n llm-judge -l app=redis

# Check Redis PVC
kubectl get pvc -n llm-judge

# Check Redis service
kubectl get svc -n llm-judge redis

# Test connection
kubectl port-forward -n llm-judge svc/redis 6379:6379 &
redis-cli ping
killall kubectl
```

### Check Terraform State

```bash
cd deploy/iac/terragrunt/dev/helm-releases

# List Terraform resources
terragrunt state list | grep redis

# Show Redis release details
terragrunt state show 'helm_release.redis_cache'
```

## Configuration

### Values File: `deploy/helm/releases/redis-values.yaml`

All Redis configuration is centralized in the values file:
- Image: `redis:7.1-alpine`
- Resources: 100m CPU, 256Mi memory (requests)
- Persistence: 10Gi gp3 volume
- Security: Non-root, no capabilities
- Health probes: Liveness and readiness

### Modify Configuration

```bash
# Edit values file
vim deploy/helm/releases/redis-values.yaml

# Apply changes
cd deploy/iac/terragrunt/dev/helm-releases
terragrunt apply
```

## Dependency Management

### Redis Depends On

- **EKS Cluster**: Kubernetes API must be available
- **Namespace**: `llm-judge` namespace must exist
- **StorageClass**: `gp3` StorageClass must exist
- **Metrics Server**: For HPA support

### Services That Depend On Redis

- **redis-service**: Microservice that interfaces with Redis
- **AppConfig**: References Redis service DNS

## Rollback

### To Previous Version

```bash
cd deploy/iac/terragrunt/dev/helm-releases

# Show Helm release history
helm history redis -n llm-judge

# Rollback to previous version
helm rollback redis -n llm-judge

# Or rollback via Terraform (restore previous state)
terragrunt apply -target=helm_release.redis_cache
```

### Complete Removal

```bash
cd deploy/iac/terragrunt/dev/helm-releases

# Destroy Redis release only
terragrunt destroy -target=helm_release.redis_cache

# Or destroy entire helm-releases module
terragrunt destroy
```

## Troubleshooting

### Pod Not Starting

```bash
# Check pod events
kubectl describe pod -n llm-judge -l app=redis

# Check pod logs
kubectl logs -n llm-judge -l app=redis

# Check Helm release status
helm status redis -n llm-judge
```

### PVC Not Binding

```bash
# Check PVC status
kubectl get pvc -n llm-judge
kubectl describe pvc redis-data -n llm-judge

# Check StorageClass
kubectl get storageclass gp3
kubectl describe storageclass gp3

# Check EBS CSI driver
kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-ebs-csi-driver
```

### Terraform Apply Fails

```bash
# Check Terraform state
cd deploy/iac/terragrunt/dev/helm-releases
terragrunt state list

# Validate Terraform configuration
terragrunt validate

# Plan changes
terragrunt plan

# Check provider versions
terragrunt providers
```

## Upgrade Path

### From Shell Scripts to Terraform

If you previously deployed Redis using shell scripts:

1. **Backup existing Redis data**
   ```bash
   kubectl exec -n llm-judge deploy/redis -- redis-cli SAVE
   kubectl cp llm-judge/redis-xxxxx:/data/dump.rdb ./backup-$(date +%Y%m%d).rdb
   ```

2. **Import existing Helm release** (if already deployed)
   ```bash
   cd deploy/iac/terragrunt/dev/helm-releases
   terragrunt import 'helm_release.redis_cache' llm-judge/redis
   ```

3. **Apply Terraform configuration**
   ```bash
   terragrunt apply
   ```

## Benefits

### Before (Shell Scripts)

- ❌ Manual deployment process
- ❌ No dependency tracking
- ❌ No state management
- ❌ Difficult to reproduce
- ❌ No version control integration

### After (Terraform Helm Provider)

- ✅ Automated deployment
- ✅ Explicit dependency chain
- ✅ State managed by Terraform
- ✅ Reproducible deployments
- ✅ GitOps-ready
- ✅ Integrated with CI/CD

## References

- **Helm Chart**: `/deploy/helm/charts/redis/`
- **Values File**: `/deploy/helm/releases/redis-values.yaml`
- **Terraform Module**: `/deploy/iac/terraform/helm-releases/`
- **Terragrunt Wrapper**: `/deploy/iac/terragrunt/dev/helm-releases/`
- **Chart Documentation**: `/deploy/helm/charts/redis/README.md`
- **Migration Guide**: `/deploy/helm/charts/redis/MIGRATION.md`
