# ========================================================================
# APPLICATION - REDIS SERVICE
# Redis caching microservice for the LLM Judge platform
# ========================================================================

resource "helm_release" "redis_service_release" {
  name      = "redis-service"
  chart     = local.llm_judge_chart_path
  namespace = kubernetes_namespace.llm_judge_namespace.metadata[0].name

  values = [
    yamlencode({
      serviceName  = var.service_names.redis
      replicaCount = var.autoscaling.services.redis.min_replicas

      image = {
        repository = "${var.ecr_repository_prefix}/${var.service_names.redis}"
        tag        = var.image_tag
        pullPolicy = "Always"
      }

      serviceAccount = {
        create = true
        name   = var.service_names.redis
        annotations = {
          "eks.amazonaws.com/role-arn" = var.iam_role_arns["redis_service"]
        }
      }

      service = {
        type          = "ClusterIP"
        containerPort = var.service_ports.redis
        port          = var.service_ports.redis
      }

      resources = {
        requests = {
          cpu    = "200m"
          memory = "256Mi"
        }
        limits = {
          cpu    = "500m"
          memory = "512Mi"
        }
      }

      autoscaling = {
        enabled                        = true
        minReplicas                    = var.autoscaling.services.redis.min_replicas
        maxReplicas                    = var.autoscaling.services.redis.max_replicas
        targetCPUUtilizationPercentage = var.autoscaling.cpu_target_percent
      }

      envFrom = [
        {
          configMapRef = {
            name = kubernetes_config_map.infra_config.metadata[0].name
          }
        }
      ]
    })
  ]

  depends_on = [
    helm_release.external_secrets_release,
    kubernetes_config_map.infra_config
  ]
}
