# LLM_Judge Observability Pipeline Plan
## Grafana Cloud + Alloy Architecture

---

## Executive Summary

This plan establishes a production-grade observability pipeline for the LLM_Judge microservices platform using **Grafana Alloy** as the telemetry collector and **Grafana Cloud** as the backend. The architecture uses multiple Alloy instances optimized for different telemetry types and is designed for seamless migration from local Kubernetes to AWS EKS.

---

## Current State Analysis

### Existing Observability (Already Implemented)

| Component | Status | Location |
|-----------|--------|----------|
| **Structured JSON Logging** | ✅ Ready | `utils/observability/logs/logger.py` |
| **OpenTelemetry Tracing** | ✅ Ready | `utils/observability/traces/tracer.py` |
| **OTLP HTTP Exporter** | ✅ Configured | Traces export to `observability.traces.collector.endpoint` |
| **W3C Trace Context** | ✅ Implemented | `utils/observability/traces/spans/spanner.py` |
| **Trace-Log Correlation** | ✅ Implemented | `trace_id` and `span_id` injected into logs |
| **Health Endpoints** | ✅ All Services | `/health` on each service |

### Gaps to Address

| Gap | Solution |
|-----|----------|
| No centralized log collection | Alloy DaemonSet scrapes container logs |
| No Prometheus metrics | Add `opentelemetry-instrumentation-*` packages |
| Traces not reaching backend | Point OTLP exporter to Alloy receiver |
| No K8s cluster metrics | Alloy scrapes kubelet, cAdvisor, kube-state-metrics |
| No node-level metrics | Alloy DaemonSet with node_exporter |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           KUBERNETES CLUSTER                                 │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        APPLICATION PODS                              │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │    │
│  │  │ Gateway  │ │Inference │ │  Judge   │ │  Redis   │ │Persistence│   │    │
│  │  │ :8000    │ │ :8003    │ │ :8004    │ │ :8001    │ │  :8002   │   │    │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘   │    │
│  │       │ OTLP       │ OTLP       │ OTLP       │ OTLP       │ OTLP    │    │
│  └───────┼────────────┼────────────┼────────────┼────────────┼─────────┘    │
│          │            │            │            │            │              │
│          └────────────┴────────────┼────────────┴────────────┘              │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    ALLOY INSTANCES (4 Types)                         │    │
│  │                                                                      │    │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │    │
│  │  │ alloy-receiver  │  │  alloy-logs     │  │ alloy-metrics   │      │    │
│  │  │ (DaemonSet)     │  │  (DaemonSet)    │  │ (StatefulSet)   │      │    │
│  │  │                 │  │                 │  │                 │      │    │
│  │  │ • OTLP gRPC     │  │ • Pod logs      │  │ • kubelet       │      │    │
│  │  │ • OTLP HTTP     │  │ • Node logs     │  │ • cAdvisor      │      │    │
│  │  │ • App traces    │  │ • Container     │  │ • kube-state    │      │    │
│  │  │ • App metrics   │  │   stdout/stderr │  │ • node_exporter │      │    │
│  │  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘      │    │
│  │           │                    │                    │               │    │
│  │  ┌─────────────────┐           │                    │               │    │
│  │  │ alloy-singleton │           │                    │               │    │
│  │  │ (Deployment x1) │           │                    │               │    │
│  │  │                 │           │                    │               │    │
│  │  │ • K8s events    │           │                    │               │    │
│  │  │ • Cluster-wide  │           │                    │               │    │
│  │  └────────┬────────┘           │                    │               │    │
│  │           │                    │                    │               │    │
│  └───────────┼────────────────────┼────────────────────┼────────────────┘    │
│              │                    │                    │                     │
└──────────────┼────────────────────┼────────────────────┼─────────────────────┘
               │                    │                    │
               └────────────────────┼────────────────────┘
                                    │
                                    ▼ OTLP/HTTP + Basic Auth
                    ┌───────────────────────────────────┐
                    │         GRAFANA CLOUD             │
                    │                                   │
                    │  ┌─────────┐ ┌─────────┐ ┌──────┐│
                    │  │  Tempo  │ │  Loki   │ │Mimir ││
                    │  │ Traces  │ │  Logs   │ │Metric││
                    │  └─────────┘ └─────────┘ └──────┘│
                    │                                   │
                    │         ┌──────────────┐         │
                    │         │   Grafana    │         │
                    │         │  Dashboards  │         │
                    │         └──────────────┘         │
                    └───────────────────────────────────┘
```

---

## Phase 1: Grafana Cloud Setup

### 1.1 Create Grafana Cloud Account

1. Go to https://grafana.com/products/cloud/
2. Sign up for **Free Tier** (includes):
   - 10k active series (Prometheus metrics)
   - 50GB logs
   - 50GB traces
   - 50GB profiles
3. Note your **Stack URL**: `https://<your-stack>.grafana.net`

### 1.2 Generate API Credentials

1. Navigate to **My Account** → **API Keys**
2. Create a new API key with:
   - **Role**: `MetricsPublisher` (or Admin for full access)
   - **Expiration**: Set appropriate TTL
3. Record these values:
   ```
   GRAFANA_CLOUD_INSTANCE_ID: <your-instance-id>
   GRAFANA_CLOUD_API_KEY: <generated-api-key>
   GRAFANA_CLOUD_OTLP_ENDPOINT: https://otlp-gateway-prod-<region>.grafana.net/otlp
   ```

### 1.3 Get OTLP Endpoint Details

1. Go to **Connections** → **Add new connection** → **OpenTelemetry (OTLP)**
2. Click **Configure**
3. Copy the endpoint URL and generate a token
4. The auth header format is: `Basic base64(<instance-id>:<api-key>)`

---

## Phase 2: Kubernetes Secrets Configuration

### 2.1 Create Grafana Cloud Secret

```yaml
# local/k8s/grafana-cloud-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: grafana-cloud-credentials
  namespace: llm-judge
type: Opaque
stringData:
  # Get these from Grafana Cloud console
  GRAFANA_CLOUD_INSTANCE_ID: "<your-instance-id>"
  GRAFANA_CLOUD_API_KEY: "<your-api-key>"
  # Region-specific endpoint (us, eu, etc.)
  GRAFANA_CLOUD_OTLP_ENDPOINT: "https://otlp-gateway-prod-us-central-0.grafana.net/otlp"
  # For Prometheus remote write
  GRAFANA_CLOUD_PROMETHEUS_ENDPOINT: "https://prometheus-prod-us-central-0.grafana.net/api/prom/push"
  GRAFANA_CLOUD_PROMETHEUS_USER: "<prometheus-user-id>"
  # For Loki
  GRAFANA_CLOUD_LOKI_ENDPOINT: "https://logs-prod-us-central-0.grafana.net/loki/api/v1/push"
  GRAFANA_CLOUD_LOKI_USER: "<loki-user-id>"
```

### 2.2 Apply Secret

```bash
# Create the secret (replace values first!)
kubectl apply -f local/k8s/grafana-cloud-secret.yaml
```

---

## Phase 3: Deploy Grafana Kubernetes Monitoring Helm Chart

This is the **recommended approach** - uses the official Grafana k8s-monitoring Helm chart which deploys all required Alloy instances automatically.

### 3.1 Add Helm Repository

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
```

### 3.2 Create Values File

```yaml
# local/k8s/helm/k8s-monitoring-values.yaml
cluster:
  name: llm-judge-cluster

# Destinations - where to send telemetry
externalServices:
  prometheus:
    host: "https://prometheus-prod-us-central-0.grafana.net"
    basicAuth:
      username: "${GRAFANA_CLOUD_PROMETHEUS_USER}"
      password: "${GRAFANA_CLOUD_API_KEY}"

  loki:
    host: "https://logs-prod-us-central-0.grafana.net"
    basicAuth:
      username: "${GRAFANA_CLOUD_LOKI_USER}"
      password: "${GRAFANA_CLOUD_API_KEY}"

  tempo:
    host: "https://otlp-gateway-prod-us-central-0.grafana.net/otlp"
    basicAuth:
      username: "${GRAFANA_CLOUD_INSTANCE_ID}"
      password: "${GRAFANA_CLOUD_API_KEY}"

# Metrics collection
metrics:
  enabled: true
  # Collect from all sources
  cadvisor:
    enabled: true
  kubelet:
    enabled: true
  kubeStateMetrics:
    enabled: true
  nodeExporter:
    enabled: true
  # Cost metrics (optional but useful)
  cost:
    enabled: true
  # Scrape Prometheus annotations
  autoDiscover:
    enabled: true
    annotations:
      scrape: "prometheus.io/scrape"
      port: "prometheus.io/port"
      path: "prometheus.io/path"

# Logs collection
logs:
  enabled: true
  pod_logs:
    enabled: true
    # Collect from all namespaces
    namespaces: []
  cluster_events:
    enabled: true

# Traces collection - CRITICAL for your app
traces:
  enabled: true
  receiver:
    grpc:
      enabled: true
      port: 4317
    http:
      enabled: true
      port: 4318

# Alloy instance configurations
alloy-metrics:
  enabled: true
  controller:
    type: statefulset
    replicas: 1
  resources:
    requests:
      cpu: 100m
      memory: 256Mi
    limits:
      cpu: 500m
      memory: 512Mi

alloy-logs:
  enabled: true
  controller:
    type: daemonset
  resources:
    requests:
      cpu: 50m
      memory: 128Mi
    limits:
      cpu: 200m
      memory: 256Mi

alloy-receiver:
  enabled: true
  controller:
    type: daemonset  # DaemonSet so apps can send to local node
  alloy:
    extraPorts:
      - name: otlp-grpc
        port: 4317
        targetPort: 4317
        protocol: TCP
      - name: otlp-http
        port: 4318
        targetPort: 4318
        protocol: TCP
  resources:
    requests:
      cpu: 100m
      memory: 256Mi
    limits:
      cpu: 500m
      memory: 512Mi

alloy-singleton:
  enabled: true
  controller:
    type: deployment
    replicas: 1
  resources:
    requests:
      cpu: 50m
      memory: 128Mi
    limits:
      cpu: 200m
      memory: 256Mi
```

### 3.3 Install the Helm Chart

```bash
# Install in llm-judge namespace
helm install grafana-k8s-monitoring grafana/k8s-monitoring \
  --namespace llm-judge \
  --values local/k8s/helm/k8s-monitoring-values.yaml \
  --set-file "externalServices.prometheus.basicAuth.password=/path/to/api-key" \
  --set-file "externalServices.loki.basicAuth.password=/path/to/api-key" \
  --set-file "externalServices.tempo.basicAuth.password=/path/to/api-key"
```

Or use the secret:

```bash
helm install grafana-k8s-monitoring grafana/k8s-monitoring \
  --namespace llm-judge \
  --values local/k8s/helm/k8s-monitoring-values.yaml \
  --set "externalServices.prometheus.basicAuth.passwordSecretName=grafana-cloud-credentials" \
  --set "externalServices.prometheus.basicAuth.passwordSecretKey=GRAFANA_CLOUD_API_KEY" \
  --set "externalServices.loki.basicAuth.passwordSecretName=grafana-cloud-credentials" \
  --set "externalServices.loki.basicAuth.passwordSecretKey=GRAFANA_CLOUD_API_KEY" \
  --set "externalServices.tempo.basicAuth.passwordSecretName=grafana-cloud-credentials" \
  --set "externalServices.tempo.basicAuth.passwordSecretKey=GRAFANA_CLOUD_API_KEY"
```

---

## Phase 4: Application Configuration Updates

### 4.1 Update AppConfig for Alloy Endpoint

Update your ConfigMap to point traces to the Alloy receiver:

```yaml
# local/k8s/configmap.yaml - ADD/UPDATE these entries
data:
  appconfig.json: |
    {
      ...existing config...

      "observability.traces.collector.endpoint": "http://grafana-k8s-monitoring-alloy-receiver.llm-judge.svc.cluster.local:4318/v1/traces",
      "observability.traces.sample_rate": 1.0,
      "observability.logs.export_to_loki": true,
      "observability.metrics.enabled": true
    }
```

### 4.2 Add OpenTelemetry Auto-Instrumentation (Optional Enhancement)

Add these packages to `requirements.txt`:

```
# OpenTelemetry Auto-Instrumentation
opentelemetry-instrumentation-fastapi==0.43b0
opentelemetry-instrumentation-httpx==0.43b0
opentelemetry-instrumentation-redis==0.43b0
opentelemetry-instrumentation-sqlalchemy==0.43b0
opentelemetry-instrumentation-boto3==0.43b0

# Metrics support
opentelemetry-exporter-otlp-proto-http==1.22.0
```

### 4.3 Update Service Deployments

Each service deployment needs environment variables for the OTLP endpoint:

```yaml
# Example: local/k8s/gateway-service.yaml
spec:
  template:
    spec:
      containers:
        - name: gateway-service
          env:
            - name: OTEL_EXPORTER_OTLP_ENDPOINT
              value: "http://grafana-k8s-monitoring-alloy-receiver:4318"
            - name: OTEL_EXPORTER_OTLP_PROTOCOL
              value: "http/protobuf"
            - name: OTEL_SERVICE_NAME
              value: "gateway-service"
            - name: OTEL_RESOURCE_ATTRIBUTES
              value: "deployment.environment=production,service.namespace=llm-judge"
```

---

## Phase 5: Alloy Receiver Service (For App Telemetry)

The Helm chart creates this, but if you need manual control:

```yaml
# local/k8s/alloy-receiver-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: alloy-receiver
  namespace: llm-judge
spec:
  selector:
    app.kubernetes.io/name: alloy-receiver
  ports:
    - name: otlp-grpc
      port: 4317
      targetPort: 4317
      protocol: TCP
    - name: otlp-http
      port: 4318
      targetPort: 4318
      protocol: TCP
  type: ClusterIP
```

---

## Phase 6: Verify Deployment

### 6.1 Check Alloy Pods

```bash
# All Alloy instances should be running
kubectl get pods -n llm-judge -l app.kubernetes.io/name=alloy

# Expected output:
# grafana-k8s-monitoring-alloy-logs-xxxxx      (one per node)
# grafana-k8s-monitoring-alloy-metrics-0       (StatefulSet)
# grafana-k8s-monitoring-alloy-receiver-xxxxx  (one per node)
# grafana-k8s-monitoring-alloy-singleton-xxxxx (single pod)
```

### 6.2 Check Alloy Logs

```bash
# Check for errors
kubectl logs -n llm-judge -l app.kubernetes.io/name=alloy-receiver --tail=100

# Look for successful exports
kubectl logs -n llm-judge -l app.kubernetes.io/name=alloy-metrics --tail=100 | grep -i "export"
```

### 6.3 Verify in Grafana Cloud

1. Go to your Grafana Cloud instance
2. Navigate to **Explore**
3. Select **Tempo** → Search for traces from `gateway-service`
4. Select **Loki** → Query: `{namespace="llm-judge"}`
5. Select **Mimir/Prometheus** → Query: `up{namespace="llm-judge"}`

---

## Phase 7: Grafana Dashboards

### 7.1 Import Pre-built Dashboards

In Grafana Cloud, import these dashboards:

| Dashboard ID | Name | Purpose |
|--------------|------|---------|
| 15760 | Kubernetes / Views / Pods | Pod resource usage |
| 15757 | Kubernetes / Views / Namespaces | Namespace overview |
| 15759 | Kubernetes / Views / Nodes | Node health |
| 17119 | Kubernetes EKS Cluster | EKS-specific metrics |
| 16686 | Jaeger-style Trace Explorer | Trace visualization |

### 7.2 Create Custom LLM_Judge Dashboard

Create a dashboard with:

1. **Request Flow Panel** (Tempo)
   - Service map showing Gateway → Inference → Judge flow
   - Latency percentiles per service

2. **Queue Health Panel** (Metrics)
   - SQS message age
   - Queue depth
   - Visibility extensions count

3. **Error Rate Panel** (Loki + Metrics)
   - Error logs by service
   - HTTP 5xx rate
   - Failed inference rate

4. **Performance Panel** (Tempo + Metrics)
   - OpenAI API latency
   - End-to-end request latency
   - Redis operation latency

---

## Phase 8: EKS Migration Considerations

### 8.1 What Changes for EKS

| Component | Local K8s | EKS |
|-----------|-----------|-----|
| Alloy Deployment | Same Helm chart | Same Helm chart |
| IRSA | N/A | Enable for AWS SDK access |
| Node Groups | Single node | Multiple nodes (Alloy DaemonSets scale automatically) |
| EBS/EFS | Local volumes | EBS CSI driver for persistent volumes |
| Load Balancer | NodePort | AWS ALB/NLB |
| Secrets | K8s Secret | AWS Secrets Manager + External Secrets Operator |

### 8.2 EKS-Specific Values

```yaml
# local/k8s/helm/k8s-monitoring-values-eks.yaml
cluster:
  name: llm-judge-eks-prod

# EKS-specific tolerations for system nodes
alloy-logs:
  controller:
    tolerations:
      - operator: Exists

alloy-receiver:
  controller:
    tolerations:
      - operator: Exists

# Use AWS-native secrets
externalServices:
  prometheus:
    basicAuth:
      passwordSecretName: grafana-cloud-credentials  # From External Secrets Operator

# Enable EKS control plane metrics
metrics:
  apiServer:
    enabled: true
  controllerManager:
    enabled: false  # Not accessible in EKS
  scheduler:
    enabled: false  # Not accessible in EKS
```

### 8.3 IRSA Setup for AWS Telemetry

```yaml
# If collecting AWS-specific metrics (CloudWatch, etc.)
apiVersion: v1
kind: ServiceAccount
metadata:
  name: alloy-metrics
  namespace: llm-judge
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::<account>:role/AlloyMetricsRole
```

---

## Phase 9: Alerting Rules

### 9.1 Create Alert Rules in Grafana Cloud

```yaml
# Alert: High Error Rate
groups:
  - name: llm-judge-alerts
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate(http_server_requests_total{namespace="llm-judge", status=~"5.."}[5m]))
          /
          sum(rate(http_server_requests_total{namespace="llm-judge"}[5m]))
          > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate in LLM Judge"

      - alert: InferenceQueueBacklog
        expr: |
          aws_sqs_approximate_number_of_messages_visible{queue_name="inference_queue"} > 100
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Inference queue backlog growing"

      - alert: HighLatency
        expr: |
          histogram_quantile(0.95,
            sum(rate(http_server_request_duration_seconds_bucket{namespace="llm-judge"}[5m])) by (le, service)
          ) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "P95 latency above 5 seconds"
```

---

## Implementation Checklist

### Phase 1: Grafana Cloud Setup
- [ ] Create Grafana Cloud account (free tier)
- [ ] Generate API key with MetricsPublisher role
- [ ] Note OTLP endpoint URL and credentials
- [ ] Verify access to Grafana, Loki, Tempo, Mimir

### Phase 2: Kubernetes Secrets
- [ ] Create `grafana-cloud-secret.yaml` with credentials
- [ ] Apply secret to `llm-judge` namespace
- [ ] Verify secret creation: `kubectl get secret grafana-cloud-credentials -n llm-judge`

### Phase 3: Deploy Alloy via Helm
- [ ] Add Grafana Helm repository
- [ ] Create `k8s-monitoring-values.yaml`
- [ ] Install Helm chart
- [ ] Verify all Alloy pods are running

### Phase 4: Application Configuration
- [ ] Update ConfigMap with Alloy receiver endpoint
- [ ] Update service deployments with OTEL env vars
- [ ] Redeploy application services
- [ ] Verify traces appear in Tempo

### Phase 5: Verification
- [ ] Check Alloy pod logs for errors
- [ ] Query Loki for application logs
- [ ] Query Tempo for distributed traces
- [ ] Query Mimir for Kubernetes metrics
- [ ] Verify trace-log correlation works

### Phase 6: Dashboards & Alerts
- [ ] Import Kubernetes dashboards
- [ ] Create custom LLM_Judge dashboard
- [ ] Configure alerting rules
- [ ] Set up notification channels (Slack, PagerDuty, etc.)

### Phase 7: EKS Preparation
- [ ] Document EKS-specific Helm values
- [ ] Plan IRSA roles for Alloy
- [ ] Test in EKS staging environment

---

## Quick Start Commands

```bash
# 1. Add Helm repo
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# 2. Create namespace if not exists
kubectl create namespace llm-judge --dry-run=client -o yaml | kubectl apply -f -

# 3. Create secret (edit values first!)
kubectl apply -f local/k8s/grafana-cloud-secret.yaml

# 4. Install monitoring stack
helm install grafana-k8s-monitoring grafana/k8s-monitoring \
  --namespace llm-judge \
  --values local/k8s/helm/k8s-monitoring-values.yaml

# 5. Verify installation
kubectl get pods -n llm-judge -l app.kubernetes.io/part-of=alloy

# 6. Check logs
kubectl logs -n llm-judge -l app.kubernetes.io/name=alloy-receiver -f
```

---

## Cost Estimation (Grafana Cloud Free Tier)

| Resource | Free Tier Limit | Expected Usage |
|----------|-----------------|----------------|
| Metrics | 10,000 active series | ~2,000 (5 services × ~400 series) |
| Logs | 50 GB/month | ~10 GB (moderate traffic) |
| Traces | 50 GB/month | ~5 GB (with sampling) |
| Profiles | 50 GB/month | Not used initially |

**Conclusion**: Free tier should be sufficient for development and moderate production workloads.

---

## References

- [Grafana Alloy Documentation](https://grafana.com/docs/alloy/latest/)
- [Grafana K8s Monitoring Helm Chart](https://github.com/grafana/k8s-monitoring-helm)
- [Grafana Cloud OTLP Setup](https://grafana.com/docs/grafana-cloud/send-data/otlp/send-data-otlp/)
- [Configure Alloy on Kubernetes](https://grafana.com/docs/alloy/latest/configure/kubernetes/)
- [EKS Monitoring Configuration](https://grafana.com/docs/grafana-cloud/monitor-infrastructure/kubernetes-monitoring/configuration/config-other-methods/config-aws-eks/)
