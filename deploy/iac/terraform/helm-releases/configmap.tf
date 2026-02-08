# ========================================================================
# HELM RELEASES MODULE - INFRASTRUCTURE CONFIGMAP
# ========================================================================

locals {
  infra_configmap_name = "infra-config"
}

resource "kubernetes_config_map" "infra_config" {
  metadata {
    name      = local.infra_configmap_name
    namespace = kubernetes_namespace.contentpulse_namespace.metadata[0].name
    labels = {}
  }

  data = {
    AWS_REGION     = var.aws_region
    AWS_ACCOUNT_ID = var.aws_account_id

    GATEWAY_SERVICE_HOST           = var.service_names.gateway
    GATEWAY_SERVICE_PORT           = tostring(var.service_ports.gateway)
    CONTENT_POLLER_SERVICE_HOST    = var.service_names.content_poller
    CONTENT_POLLER_SERVICE_PORT    = tostring(var.service_ports.content_poller)
    CONTENT_PROCESSOR_SERVICE_HOST = var.service_names.content_processor
    CONTENT_PROCESSOR_SERVICE_PORT = tostring(var.service_ports.content_processor)
    QUERY_ENGINE_SERVICE_HOST      = var.service_names.query_engine
    QUERY_ENGINE_SERVICE_PORT      = tostring(var.service_ports.query_engine)

    REDIS_CACHE_HOST = var.infrastructure_endpoints.redis_cache.host
    REDIS_CACHE_PORT = tostring(var.infrastructure_endpoints.redis_cache.port)

    KAFKA_BOOTSTRAP_SERVERS = var.kafka_bootstrap_servers

    SQS_CONTENT_PROCESSING_QUEUE_URL = var.sqs_queue_urls["content_processing"]
    SQS_QUERY_ANSWERING_QUEUE_URL    = var.sqs_queue_urls["query_answering"]

    SNS_CONTENT_PROCESSING_TOPIC_ARN = var.sns_topic_arns["content_processing"]
    SNS_QUERY_ANSWERING_TOPIC_ARN    = var.sns_topic_arns["query_answering"]

    APPCONFIG_APPLICATION_ID = var.appconfig_ids.application_id
    APPCONFIG_ENVIRONMENT_ID = var.appconfig_ids.environment_id
    APPCONFIG_PROFILE_ID     = var.appconfig_ids.profile_id

    OTEL_EXPORTER_OTLP_TRACES_ENDPOINT = "http://alloy-traces.${var.observability_config.namespace}.svc.cluster.local:4318/v1/traces"

    ENVIRONMENT = var.environment
    NAMESPACE   = var.namespace
  }
}
