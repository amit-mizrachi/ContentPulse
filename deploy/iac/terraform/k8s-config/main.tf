# ========================================================================
# KUBERNETES CONFIGMAP - INFRA CONFIG
# ========================================================================
# This module creates a ConfigMap containing all infrastructure configuration
# values from Terragrunt. This is the BRIDGE between Terraform (SSOT) and
# Kubernetes applications.
#
# Pattern: "Infra-Output" - Terraform writes, Helm/K8s reads
# ========================================================================

resource "kubernetes_config_map" "infra_config" {
  metadata {
    name      = "infra-config"
    namespace = var.namespace
    labels = {
      "app.kubernetes.io/managed-by" = "terraform"
      "app.kubernetes.io/part-of"    = var.project_name
    }
  }

  data = {
    # ========================================================================
    # AWS CONFIGURATION
    # ========================================================================
    AWS_REGION     = var.aws_region
    AWS_ACCOUNT_ID = var.aws_account_id

    # ========================================================================
    # SERVICE PORTS
    # ========================================================================
    PORT_GATEWAY     = tostring(var.service_ports.gateway)
    PORT_REDIS       = tostring(var.service_ports.redis)
    PORT_PERSISTENCE = tostring(var.service_ports.persistence)
    PORT_INFERENCE   = tostring(var.service_ports.inference)
    PORT_JUDGE       = tostring(var.service_ports.judge)

    # ========================================================================
    # INFRASTRUCTURE PORTS
    # ========================================================================
    PORT_REDIS_CACHE = tostring(var.infrastructure_ports.redis_cache)
    PORT_MYSQL       = tostring(var.infrastructure_ports.mysql)
    PORT_DNS         = tostring(var.infrastructure_ports.dns)
    PORT_HTTPS       = tostring(var.infrastructure_ports.https)

    # ========================================================================
    # SERVICE NAMES (for service discovery)
    # ========================================================================
    SERVICE_NAME_GATEWAY     = var.service_names.gateway
    SERVICE_NAME_REDIS       = var.service_names.redis
    SERVICE_NAME_PERSISTENCE = var.service_names.persistence
    SERVICE_NAME_INFERENCE   = var.service_names.inference
    SERVICE_NAME_JUDGE       = var.service_names.judge

    # ========================================================================
    # HEALTH CHECK CONFIGURATION
    # ========================================================================
    HEALTH_CHECK_INTERVAL = tostring(var.health_check.interval_seconds)
    HEALTH_CHECK_TIMEOUT  = tostring(var.health_check.timeout_seconds)
    HEALTH_CHECK_RETRIES  = tostring(var.health_check.retries)
    HEALTH_CHECK_PATH     = var.health_check.path

    # ========================================================================
    # HTTP CLIENT TIMEOUTS
    # ========================================================================
    HTTP_TIMEOUT_REDIS           = tostring(var.http_timeouts.redis_client)
    HTTP_TIMEOUT_PERSISTENCE     = tostring(var.http_timeouts.persistence_client)
    HTTP_TIMEOUT_JUDGE_INFERENCE = tostring(var.http_timeouts.judge_inference_client)

    # ========================================================================
    # AUTOSCALING
    # ========================================================================
    AUTOSCALING_CPU_TARGET = tostring(var.autoscaling_cpu_target)

    # ========================================================================
    # VPC
    # ========================================================================
    VPC_CIDR = var.vpc_cidr

    # ========================================================================
    # ECR
    # ========================================================================
    ECR_REPOSITORY_PREFIX = var.ecr_repository_prefix
    ECR_IMAGE_TAG         = var.ecr_image_tag
  }
}

# ========================================================================
# KUBERNETES CONFIGMAP - SQS WORKER CONFIG
# ========================================================================
# Separate ConfigMap for SQS worker configuration (more complex structure)
# ========================================================================

resource "kubernetes_config_map" "sqs_config" {
  metadata {
    name      = "sqs-config"
    namespace = var.namespace
    labels = {
      "app.kubernetes.io/managed-by" = "terraform"
      "app.kubernetes.io/part-of"    = var.project_name
    }
  }

  data = {
    # Worker settings
    SQS_MAX_WORKER_COUNT                      = tostring(var.sqs_worker_config.max_worker_count)
    SQS_VISIBILITY_TIMEOUT_SECONDS            = tostring(var.sqs_worker_config.visibility_timeout_seconds)
    SQS_VISIBILITY_EXTENSION_INTERVAL_SECONDS = tostring(var.sqs_worker_config.visibility_extension_interval_seconds)
    SQS_MAX_MESSAGE_PROCESS_TIME_SECONDS      = tostring(var.sqs_worker_config.max_message_process_time_seconds)
    SQS_CONSUMER_SHUTDOWN_TIMEOUT_SECONDS     = tostring(var.sqs_worker_config.consumer_shutdown_timeout_seconds)
    SQS_SECONDS_BETWEEN_RECEIVE_ATTEMPTS      = tostring(var.sqs_worker_config.seconds_between_receive_attempts)
    SQS_WAIT_TIME_SECONDS                     = tostring(var.sqs_worker_config.wait_time_seconds)
  }
}
