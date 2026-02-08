# ========================================================================
# INFRASTRUCTURE - REDIS CACHE
# Kubernetes-native Redis deployment for caching
# ========================================================================

resource "helm_release" "redis_cache_release" {
  name             = "redis"
  repository       = "https://charts.bitnami.com/bitnami"
  chart            = "redis"
  version          = "18.6.1"
  namespace        = kubernetes_namespace.llm_judge_namespace.metadata[0].name
  create_namespace = false

  values = [<<-EOT
image:
  tag: "7.2"

fullnameOverride: "redis"

architecture: standalone

auth:
  enabled: false

master:
  service:
    type: ClusterIP
    ports:
      redis: 6379

  resources:
    requests:
      cpu: 100m
      memory: 256Mi
    limits:
      cpu: 500m
      memory: 512Mi

  persistence:
    enabled: true
    storageClass: "gp3"
    accessModes:
      - ReadWriteOnce
    size: 10Gi

  nodeSelector:
    role: application

  podSecurityContext:
    fsGroup: 1001

  containerSecurityContext:
    runAsUser: 1001
    runAsNonRoot: true

commonConfiguration: |-
  maxmemory 256mb
  maxmemory-policy allkeys-lru
  save 900 1 300 10 60 10000
  appendonly yes
  appendfsync everysec
EOT
  ]

  depends_on = [
    helm_release.metrics_server_release,
    kubernetes_namespace.llm_judge_namespace,
    kubernetes_storage_class.gp3
  ]
}
