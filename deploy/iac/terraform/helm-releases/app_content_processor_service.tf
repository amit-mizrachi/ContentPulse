# ========================================================================
# APPLICATION - CONTENT PROCESSOR SERVICE
# Processes content with conditional GPU/CPU scheduling
# ========================================================================

locals {
  content_processor_gpu_mode = try(var.inference_config.content_processor.inference_mode, "remote") == "local"
}

resource "helm_release" "content_processor_service_release" {
  name      = "content-processor-service"
  chart     = local.contentpulse_chart_path
  namespace = kubernetes_namespace.contentpulse_namespace.metadata[0].name

  values = [
    yamlencode({
      serviceName  = var.service_names.content_processor
      replicaCount = local.content_processor_gpu_mode ? 0 : var.autoscaling.services.content_processor.min_replicas

      image = {
        repository = "${var.ecr_repository_prefix}/inference-service"
        tag        = var.image_tag
        pullPolicy = "Always"
      }

      command = ["python", "-m", "src.services.content_processor.server"]

      serviceAccount = {
        create = true
        name   = var.service_names.content_processor
        annotations = {
          "eks.amazonaws.com/role-arn" = var.iam_role_arns["content_processor_service"]
        }
      }

      service = {
        name          = var.service_names.content_processor
        type          = "ClusterIP"
        containerPort = var.service_ports.content_processor
        port          = var.service_ports.content_processor
        portKey       = "PORT_CONTENT_PROCESSOR"
      }

      resources = local.content_processor_gpu_mode ? {
        requests = { cpu = "500m", memory = "1Gi", "nvidia.com/gpu" = "1" }
        limits   = { cpu = "2000m", memory = "4Gi", "nvidia.com/gpu" = "1" }
      } : {
        requests = { cpu = "500m", memory = "1Gi" }
        limits   = { cpu = "2000m", memory = "2Gi" }
      }

      nodeSelector = local.content_processor_gpu_mode ? {
        "nvidia.com/gpu" = "true"
      } : {
        role = "application"
      }

      tolerations = local.content_processor_gpu_mode ? [
        { key = "nvidia.com/gpu", value = "true", effect = "NoSchedule" }
      ] : []

      autoscaling = {
        enabled     = !local.content_processor_gpu_mode
        minReplicas = var.autoscaling.services.content_processor.min_replicas
        maxReplicas = var.autoscaling.services.content_processor.max_replicas
        targetCPUUtilizationPercentage = var.autoscaling.cpu_target_percent
      }

      keda = {
        enabled         = local.content_processor_gpu_mode
        pollingInterval = 30
        cooldownPeriod  = 1800
        minReplicas     = 0
        maxReplicas     = 1
        triggers = local.content_processor_gpu_mode ? [
          {
            type = "kafka"
            metadata = {
              bootstrapServers = var.kafka_bootstrap_servers
              consumerGroup    = var.kafka_consumer_groups.content_processor
              topic            = var.kafka_topics.content_processing
              lagThreshold     = "5"
            }
          }
        ] : []
      }

      inferenceMode = try(var.inference_config.content_processor.inference_mode, "remote")

      env = [
        { name = "SERVICE_NAME", value = var.service_names.content_processor }
      ]

      envFrom = [{ configMapRef = { name = kubernetes_config_map.infra_config.metadata[0].name } }]
    })
  ]

  depends_on = [
    helm_release.external_secrets_release,
    kubernetes_config_map.infra_config
  ]
}
