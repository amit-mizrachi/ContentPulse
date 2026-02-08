# ========================================================================
# SYSTEM - KUBE STATE METRICS
# Cluster-level Kubernetes object metrics for Alloy to scrape
# ========================================================================

resource "helm_release" "kube_state_metrics_release" {
  name       = "kube-state-metrics"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-state-metrics"
  namespace  = "kube-system"
  version    = var.observability_config.kube_state_metrics.chart_version

  set {
    name  = "resources.requests.cpu"
    value = "50m"
  }

  set {
    name  = "resources.requests.memory"
    value = "64Mi"
  }

  set {
    name  = "resources.limits.cpu"
    value = "200m"
  }

  set {
    name  = "resources.limits.memory"
    value = "256Mi"
  }

  set {
    name  = "nodeSelector.role"
    value = "system"
  }

  depends_on = [
    helm_release.metrics_server_release
  ]
}
