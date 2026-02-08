# ========================================================================
# APPLICATION - INFERENCE SERVICE
# LLM inference processing from SQS queue
# ========================================================================

resource "helm_release" "inference_service_release" {
  name      = "inference-service"
  chart     = local.llm_judge_chart_path
  namespace = kubernetes_namespace.llm_judge_namespace.metadata[0].name

  values = [
    yamlencode({
      serviceName  = var.service_names.inference
      replicaCount = var.autoscaling.services.inference.min_replicas

      image = {
        repository = "${var.ecr_repository_prefix}/${var.service_names.inference}"
        tag        = var.image_tag
        pullPolicy = "Always"
      }

      serviceAccount = {
        create = true
        name   = var.service_names.inference
        annotations = {
          "eks.amazonaws.com/role-arn" = var.iam_role_arns["inference_service"]
        }
      }

      service = {
        type          = "ClusterIP"
        containerPort = var.service_ports.inference
        port          = var.service_ports.inference
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
        minReplicas                    = var.autoscaling.services.inference.min_replicas
        maxReplicas                    = var.autoscaling.services.inference.max_replicas
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
