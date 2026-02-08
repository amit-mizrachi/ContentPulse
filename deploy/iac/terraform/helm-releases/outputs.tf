# ========================================================================
# HELM RELEASES MODULE - OUTPUTS
# ========================================================================

output "namespace" {
  description = "Application namespace details"
  value = {
    name = kubernetes_namespace.contentpulse_namespace.metadata[0].name
    uid  = kubernetes_namespace.contentpulse_namespace.metadata[0].uid
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
    strimzi_operator = {
      name      = helm_release.strimzi_operator_release.name
      namespace = helm_release.strimzi_operator_release.namespace
      version   = helm_release.strimzi_operator_release.version
      status    = helm_release.strimzi_operator_release.status
    }
    kube_state_metrics = {
      name      = helm_release.kube_state_metrics_release.name
      namespace = helm_release.kube_state_metrics_release.namespace
      version   = helm_release.kube_state_metrics_release.version
      status    = helm_release.kube_state_metrics_release.status
    }
    alloy_logs_metrics = {
      name      = helm_release.alloy_daemonset_release.name
      namespace = helm_release.alloy_daemonset_release.namespace
      version   = helm_release.alloy_daemonset_release.version
      status    = helm_release.alloy_daemonset_release.status
    }
    alloy_traces = {
      name      = helm_release.alloy_traces_release.name
      namespace = helm_release.alloy_traces_release.namespace
      version   = helm_release.alloy_traces_release.version
      status    = helm_release.alloy_traces_release.status
    }
  }
}

output "alloy_trace_receiver_endpoint" {
  description = "Alloy OTLP trace receiver endpoint for application configuration"
  value = {
    otlp_http = "http://alloy-traces.${var.observability_config.namespace}.svc.cluster.local:4318/v1/traces"
    otlp_grpc = "alloy-traces.${var.observability_config.namespace}.svc.cluster.local:4317"
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
    content_poller_service = {
      name      = helm_release.content_poller_service_release.name
      namespace = helm_release.content_poller_service_release.namespace
      status    = helm_release.content_poller_service_release.status
    }
    content_processor_service = {
      name      = helm_release.content_processor_service_release.name
      namespace = helm_release.content_processor_service_release.namespace
      status    = helm_release.content_processor_service_release.status
    }
    query_engine_service = {
      name      = helm_release.query_engine_service_release.name
      namespace = helm_release.query_engine_service_release.namespace
      status    = helm_release.query_engine_service_release.status
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
