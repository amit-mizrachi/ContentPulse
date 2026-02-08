# ========================================================================
# HELM RELEASES MODULE - OUTPUTS
# ========================================================================

output "namespace" {
  description = "Application namespace details"
  value = {
    name = kubernetes_namespace.llm_judge_namespace.metadata[0].name
    uid  = kubernetes_namespace.llm_judge_namespace.metadata[0].uid
  }
}

output "system_releases" {
  description = "System Helm releases status"
  value = {
    metrics_server = {
      name      = helm_release.metrics_server_release.name
      namespace = helm_release.metrics_server_release.namespace
      version   = helm_release.metrics_server_release.version
      status    = helm_release.metrics_server_release.status
    }
    aws_load_balancer_controller = {
      name      = helm_release.alb_controller_release.name
      namespace = helm_release.alb_controller_release.namespace
      version   = helm_release.alb_controller_release.version
      status    = helm_release.alb_controller_release.status
    }
    external_secrets = {
      name      = helm_release.external_secrets_release.name
      namespace = helm_release.external_secrets_release.namespace
      version   = helm_release.external_secrets_release.version
      status    = helm_release.external_secrets_release.status
    }
    cluster_autoscaler = {
      name      = helm_release.cluster_autoscaler_release.name
      namespace = helm_release.cluster_autoscaler_release.namespace
      version   = helm_release.cluster_autoscaler_release.version
      status    = helm_release.cluster_autoscaler_release.status
    }
  }
}

output "infrastructure_releases" {
  description = "Infrastructure Helm releases status"
  value = {
    redis_cache = {
      name      = helm_release.redis_cache_release.name
      namespace = helm_release.redis_cache_release.namespace
      status    = helm_release.redis_cache_release.status
    }
  }
}

output "application_releases" {
  description = "Application Helm releases status"
  value = {
    gateway_service = {
      name      = helm_release.gateway_service_release.name
      namespace = helm_release.gateway_service_release.namespace
      status    = helm_release.gateway_service_release.status
    }
    redis_service = {
      name      = helm_release.redis_service_release.name
      namespace = helm_release.redis_service_release.namespace
      status    = helm_release.redis_service_release.status
    }
    persistence_service = {
      name      = helm_release.persistence_service_release.name
      namespace = helm_release.persistence_service_release.namespace
      status    = helm_release.persistence_service_release.status
    }
    inference_service = {
      name      = helm_release.inference_service_release.name
      namespace = helm_release.inference_service_release.namespace
      status    = helm_release.inference_service_release.status
    }
    judge_service = {
      name      = helm_release.judge_service_release.name
      namespace = helm_release.judge_service_release.namespace
      status    = helm_release.judge_service_release.status
    }
  }
}

output "configmap_name" {
  description = "Infrastructure ConfigMap name"
  value       = kubernetes_config_map.infra_config.metadata[0].name
}

output "secret_store_name" {
  description = "Cluster SecretStore name"
  value       = kubernetes_manifest.cluster_secret_store.manifest.metadata.name
}
