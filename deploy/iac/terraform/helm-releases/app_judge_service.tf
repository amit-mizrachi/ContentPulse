# ========================================================================
# APPLICATION - JUDGE SERVICE
# LLM response evaluation and scoring service
# ========================================================================

resource "helm_release" "judge_service_release" {
  name      = "judge-service"
  chart     = local.llm_judge_chart_path
  namespace = kubernetes_namespace.llm_judge_namespace.metadata[0].name

  values = [
    yamlencode({
      serviceName  = var.service_names.judge
      replicaCount = var.autoscaling.services.judge.min_replicas

      image = {
        repository = "${var.ecr_repository_prefix}/${var.service_names.judge}"
        tag        = var.image_tag
        pullPolicy = "Always"
      }

      serviceAccount = {
        create = true
        name   = var.service_names.judge
        annotations = {
          "eks.amazonaws.com/role-arn" = var.iam_role_arns["judge_service"]
        }
      }

      service = {
        type          = "ClusterIP"
        containerPort = var.service_ports.judge
        port          = var.service_ports.judge
      }

      resources = {
        requests = {
          cpu    = "500m"
          memory = "1Gi"
        }
        limits = {
          cpu    = "2000m"
          memory = "2Gi"
        }
      }

      autoscaling = {
        enabled                        = true
        minReplicas                    = var.autoscaling.services.judge.min_replicas
        maxReplicas                    = var.autoscaling.services.judge.max_replicas
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
