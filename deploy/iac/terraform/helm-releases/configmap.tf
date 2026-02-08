# ========================================================================
# HELM RELEASES MODULE - INFRASTRUCTURE CONFIGMAP
# ========================================================================

locals {
  infra_configmap_name = "infra-config"
}

resource "kubernetes_config_map" "infra_config" {
  metadata {
    name      = local.infra_configmap_name
    namespace = kubernetes_namespace.llm_judge_namespace.metadata[0].name

    labels = {
    }
  }

  data = {
    # AWS Configuration
    AWS_REGION     = var.aws_region
    AWS_ACCOUNT_ID = var.aws_account_id

    # Service Endpoints
    GATEWAY_SERVICE_HOST     = var.service_names.gateway
    GATEWAY_SERVICE_PORT     = tostring(var.service_ports.gateway)
    REDIS_SERVICE_HOST       = var.service_names.redis
    REDIS_SERVICE_PORT       = tostring(var.service_ports.redis)
    PERSISTENCE_SERVICE_HOST = var.service_names.persistence
    PERSISTENCE_SERVICE_PORT = tostring(var.service_ports.persistence)
    INFERENCE_SERVICE_HOST   = var.service_names.inference
    INFERENCE_SERVICE_PORT   = tostring(var.service_ports.inference)
    JUDGE_SERVICE_HOST       = var.service_names.judge
    JUDGE_SERVICE_PORT       = tostring(var.service_ports.judge)

    # Infrastructure Endpoints
    REDIS_CACHE_HOST = var.infrastructure_endpoints.redis_cache.host
    REDIS_CACHE_PORT = tostring(var.infrastructure_endpoints.redis_cache.port)
    RDS_HOST         = var.infrastructure_endpoints.rds.host
    RDS_PORT         = tostring(var.infrastructure_endpoints.rds.port)

    # SQS Queue URLs
    SQS_INFERENCE_QUEUE_URL = var.sqs_queue_urls["inference"]
    SQS_JUDGE_QUEUE_URL     = var.sqs_queue_urls["judge"]

    # SNS Topic ARNs
    SNS_INFERENCE_TOPIC_ARN = var.sns_topic_arns["inference"]
    SNS_JUDGE_TOPIC_ARN     = var.sns_topic_arns["judge"]

    # AppConfig IDs
    APPCONFIG_APPLICATION_ID = var.appconfig_ids.application_id
    APPCONFIG_ENVIRONMENT_ID = var.appconfig_ids.environment_id
    APPCONFIG_PROFILE_ID     = var.appconfig_ids.profile_id

    # Environment
    ENVIRONMENT = var.environment
    NAMESPACE   = var.namespace
  }
}
