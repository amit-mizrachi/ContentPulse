# ========================================================================
# APPLICATION - PERSISTENCE SERVICE
# Database access layer with RDS credentials from Secrets Manager
# ========================================================================

resource "helm_release" "persistence_service_release" {
  name      = "persistence-service"
  chart     = local.llm_judge_chart_path
  namespace = kubernetes_namespace.llm_judge_namespace.metadata[0].name

  values = [
    yamlencode({
      serviceName  = var.service_names.persistence
      replicaCount = var.autoscaling.services.persistence.min_replicas

      image = {
        repository = "${var.ecr_repository_prefix}/${var.service_names.persistence}"
        tag        = var.image_tag
        pullPolicy = "Always"
      }

      serviceAccount = {
        create = true
        name   = var.service_names.persistence
        annotations = {
          "eks.amazonaws.com/role-arn" = var.iam_role_arns["persistence_service"]
        }
      }

      service = {
        type          = "ClusterIP"
        containerPort = var.service_ports.persistence
        port          = var.service_ports.persistence
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
        minReplicas                    = var.autoscaling.services.persistence.min_replicas
        maxReplicas                    = var.autoscaling.services.persistence.max_replicas
        targetCPUUtilizationPercentage = var.autoscaling.cpu_target_percent
      }

      externalSecret = {
        enabled = true
        name    = "rds-credentials"
        secretStoreRef = {
          name = kubernetes_manifest.cluster_secret_store.manifest.metadata.name
          kind = "ClusterSecretStore"
        }
        remoteKey = var.secrets_config.rds_credentials.name
      }

      envFrom = [
        {
          configMapRef = {
            name = kubernetes_config_map.infra_config.metadata[0].name
          }
        },
        {
          secretRef = {
            name = "rds-credentials"
          }
        }
      ]
    })
  ]

  depends_on = [
    helm_release.external_secrets_release,
    kubernetes_config_map.infra_config,
    kubernetes_manifest.cluster_secret_store
  ]
}
