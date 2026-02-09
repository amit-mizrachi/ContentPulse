# ========================================================================
# APPLICATION - GATEWAY SERVICE
# API Gateway / Entry point for the simple_sport_news platform
# ========================================================================

resource "helm_release" "gateway_service_release" {
  name      = "gateway-service"
  chart     = local.simple_sport_news_chart_path
  namespace = kubernetes_namespace.simple_sport_news_namespace.metadata[0].name

  values = [
    yamlencode({
      serviceName  = var.service_names.gateway
      replicaCount = var.autoscaling.services.gateway.min_replicas

      image = {
        repository = "${var.ecr_repository_prefix}/${var.service_names.gateway}"
        tag        = var.image_tag
        pullPolicy = "Always"
      }

      serviceAccount = {
        create = true
        name   = var.service_names.gateway
        annotations = {
          "eks.amazonaws.com/role-arn" = var.iam_role_arns["gateway_service"]
        }
      }

      service = {
        name          = var.service_names.gateway
        type          = "ClusterIP"
        containerPort = var.service_ports.gateway
        port          = var.service_ports.gateway
        portKey       = "PORT_GATEWAY"
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
        minReplicas                    = var.autoscaling.services.gateway.min_replicas
        maxReplicas                    = var.autoscaling.services.gateway.max_replicas
        targetCPUUtilizationPercentage = var.autoscaling.cpu_target_percent
      }

      ingress = {
        enabled   = true
        className = "alb"
        annotations = {
          "alb.ingress.kubernetes.io/scheme"           = "internet-facing"
          "alb.ingress.kubernetes.io/target-type"      = "ip"
          "alb.ingress.kubernetes.io/healthcheck-path" = "/health"
          "alb.ingress.kubernetes.io/listen-ports"     = "[{\"HTTP\": 80}]"
          "alb.ingress.kubernetes.io/group.name"       = "simple-sport-news"
        }
        hosts = [
          {
            host = ""
            paths = [
              { path = "/", pathType = "Prefix" }
            ]
          }
        ]
        tls = []
      }

      env = [
        { name = "SERVICE_NAME", value = var.service_names.gateway }
      ]

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
