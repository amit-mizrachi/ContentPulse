# ========================================================================
# APPLICATION - CONTENT POLLER SERVICE
# Polls content sources and publishes to processing pipeline
# ========================================================================

resource "helm_release" "content_poller_service_release" {
  name      = "content-poller-service"
  chart     = local.simple_sport_news_chart_path
  namespace = kubernetes_namespace.simple_sport_news_namespace.metadata[0].name

  values = [
    yamlencode({
      serviceName  = var.service_names.content_poller
      replicaCount = var.autoscaling.services.content_poller.min_replicas

      image = {
        repository = "${var.ecr_repository_prefix}/${var.service_names.content_poller}"
        tag        = var.image_tag
        pullPolicy = "Always"
      }

      serviceAccount = {
        create = true
        name   = var.service_names.content_poller
        annotations = {
          "eks.amazonaws.com/role-arn" = var.iam_role_arns["content_poller_service"]
        }
      }

      service = {
        name          = var.service_names.content_poller
        type          = "ClusterIP"
        containerPort = var.service_ports.content_poller
        port          = var.service_ports.content_poller
        portKey       = "PORT_CONTENT_POLLER"
      }

      resources = {
        requests = { cpu = "100m", memory = "256Mi" }
        limits   = { cpu = "500m", memory = "512Mi" }
      }

      autoscaling = {
        enabled                        = true
        minReplicas                    = var.autoscaling.services.content_poller.min_replicas
        maxReplicas                    = var.autoscaling.services.content_poller.max_replicas
        targetCPUUtilizationPercentage = var.autoscaling.cpu_target_percent
      }

      env = [
        { name = "SERVICE_NAME", value = var.service_names.content_poller }
      ]

      envFrom = [{ configMapRef = { name = kubernetes_config_map.infra_config.metadata[0].name } }]
    })
  ]

  depends_on = [
    helm_release.external_secrets_release,
    kubernetes_config_map.infra_config
  ]
}
