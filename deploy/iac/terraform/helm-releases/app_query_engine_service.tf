# ========================================================================
# APPLICATION - QUERY ENGINE SERVICE
# Query answering service, always on CPU nodes
# ========================================================================

resource "helm_release" "query_engine_service_release" {
  name      = "query-engine-service"
  chart     = local.simple_sport_news_chart_path
  namespace = kubernetes_namespace.simple_sport_news_namespace.metadata[0].name

  values = [
    yamlencode({
      serviceName  = var.service_names.query_engine
      replicaCount = var.autoscaling.services.query_engine.min_replicas

      image = {
        repository = "${var.ecr_repository_prefix}/inference-service"
        tag        = var.image_tag
        pullPolicy = "Always"
      }

      command = ["python", "-m", "src.services.query_engine.server"]

      serviceAccount = {
        create = true
        name   = var.service_names.query_engine
        annotations = {
          "eks.amazonaws.com/role-arn" = var.iam_role_arns["query_engine_service"]
        }
      }

      service = {
        name          = var.service_names.query_engine
        type          = "ClusterIP"
        containerPort = var.service_ports.query_engine
        port          = var.service_ports.query_engine
        portKey       = "PORT_QUERY_ENGINE"
      }

      resources = {
        requests = { cpu = "500m", memory = "1Gi" }
        limits   = { cpu = "2000m", memory = "2Gi" }
      }

      autoscaling = {
        enabled                        = true
        minReplicas                    = var.autoscaling.services.query_engine.min_replicas
        maxReplicas                    = var.autoscaling.services.query_engine.max_replicas
        targetCPUUtilizationPercentage = var.autoscaling.cpu_target_percent
      }

      env = [
        { name = "SERVICE_NAME", value = var.service_names.query_engine }
      ]

      envFrom = [{ configMapRef = { name = kubernetes_config_map.infra_config.metadata[0].name } }]
    })
  ]

  depends_on = [
    helm_release.external_secrets_release,
    kubernetes_config_map.infra_config
  ]
}
