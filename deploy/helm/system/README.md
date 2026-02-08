# Helm System Charts

This directory contains value files for deploying EKS system components.

## Components

| Chart | Purpose | Helm Repo |
|-------|---------|-----------|
| aws-load-balancer-controller | Manage ALB/NLB for Ingress | eks/aws-load-balancer-controller |
| external-secrets | Sync AWS Secrets Manager to K8s Secrets | external-secrets/external-secrets |
| metrics-server | Enable HPA pod autoscaling | metrics-server/metrics-server |
| cluster-autoscaler | Scale EKS node groups | autoscaler/cluster-autoscaler |

## Deployment Order

1. metrics-server (HPA dependency)
2. aws-load-balancer-controller (Ingress dependency)
3. external-secrets (Secrets dependency)
4. cluster-autoscaler (Node scaling)

## Usage

Deploy using the main deploy script:

```bash
cd helm
./deploy.sh --system-only
```

Or deploy individually:

```bash
# Add repos
helm repo add eks https://aws.github.io/eks-charts
helm repo add external-secrets https://charts.external-secrets.io
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/
helm repo add autoscaler https://kubernetes.github.io/autoscaler
helm repo update

# Deploy
helm upgrade --install metrics-server metrics-server/metrics-server \
  -n kube-system -f system/metrics-server-values.yaml

helm upgrade --install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system -f system/aws-lb-controller-values.yaml

helm upgrade --install external-secrets external-secrets/external-secrets \
  -n external-secrets-system --create-namespace -f system/external-secrets-values.yaml

helm upgrade --install cluster-autoscaler autoscaler/cluster-autoscaler \
  -n kube-system -f system/cluster-autoscaler-values.yaml
```
