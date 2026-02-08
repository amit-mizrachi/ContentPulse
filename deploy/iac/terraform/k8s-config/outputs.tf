# ========================================================================
# OUTPUTS - K8S CONFIG MODULE
# ========================================================================

output "infra_config_name" {
  description = "Name of the infra-config ConfigMap"
  value       = kubernetes_config_map.infra_config.metadata[0].name
}

output "sqs_config_name" {
  description = "Name of the sqs-config ConfigMap"
  value       = kubernetes_config_map.sqs_config.metadata[0].name
}

output "namespace" {
  description = "Namespace where ConfigMaps are created"
  value       = var.namespace
}
