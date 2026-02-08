# ========================================================================
# LLM JUDGE - GLOBAL CONFIGURATION
# Single Source of Truth for LLM Judge Infrastructure
# ========================================================================
# IMPORTANT: This file is the ONLY place to define configuration values.
# All other files (Helm, Docker, Python) should reference these values.
# ========================================================================

locals {
  # ========================================================================
  # CORE ENVIRONMENT CONFIGURATION
  # ========================================================================
  aws_account_id     = "640056739274"
  aws_region         = "ap-south-1"   # Mumbai - cost optimized
  environment        = "dev"          # dev | staging | prod
  project_name       = "llm-judge"
  namespace          = "llm-judge"    # Kubernetes namespace

  # ========================================================================
  # SERVICE PORTS - SINGLE SOURCE OF TRUTH
  # ========================================================================
  service_ports = {
    gateway     = 8000
    redis       = 8001    # Redis service (not Redis cache)
    persistence = 8002
    inference   = 8003
    judge       = 8004
  }

  # ========================================================================
  # INFRASTRUCTURE PORTS
  # ========================================================================
  infrastructure_ports = {
    redis_cache = 6379
    mysql       = 3306
    dns         = 53
    https       = 443
    http        = 80
  }

  # ========================================================================
  # SERVICE NAMES - SINGLE SOURCE OF TRUTH
  # ========================================================================
  service_names = {
    gateway     = "gateway-service"
    redis       = "redis-service"
    persistence = "persistence-service"
    inference   = "inference-service"
    judge       = "judge-service"
  }

  # ========================================================================
  # HEALTH CHECK CONFIGURATION
  # ========================================================================
  health_check = {
    interval_seconds = 10
    timeout_seconds  = 5
    retries          = 5
    path             = "/health"
  }

  # ========================================================================
  # HTTP CLIENT TIMEOUTS
  # ========================================================================
  http_timeouts = {
    redis_client           = 30.0
    persistence_client     = 30.0
    judge_inference_client = 120.0
  }

  # ========================================================================
  # SQS CONFIGURATION - COMPLETE
  # ========================================================================
  sqs_config = {
    queue_names = {
      inference = "inference"
      judge     = "judge"
    }

    queue_subscriptions = {
      inference = ["inference"]
      judge     = ["judge"]
    }

    queue_properties = {
      delay_seconds             = 0
      max_message_size          = 262144   # 256 KB
      message_retention_seconds = 1209600  # 14 days
      receive_wait_time_seconds = 20       # Long polling
    }

    queue_visibility_timeout_seconds = {
      inference = 300
      judge     = 300
    }

    queue_max_receive_count = {
      inference = 3
      judge     = 3
    }

    # Worker/Consumer settings (used by Python services)
    worker_config = {
      max_worker_count                      = 10
      visibility_timeout_seconds            = 300
      visibility_extension_interval_seconds = 30
      max_message_process_time_seconds      = 600
      consumer_shutdown_timeout_seconds     = 30
      seconds_between_receive_attempts      = 1
      wait_time_seconds                     = 20
    }
  }

  # ========================================================================
  # AUTOSCALING CONFIGURATION
  # ========================================================================
  autoscaling = {
    cpu_target_percent = 70
    services = {
      gateway = {
        min_replicas = 2
        max_replicas = 10
      }
      redis = {
        min_replicas = 2
        max_replicas = 5
      }
      persistence = {
        min_replicas = 2
        max_replicas = 8
      }
      inference = {
        min_replicas = 2
        max_replicas = 20
      }
      judge = {
        min_replicas = 2
        max_replicas = 15
      }
    }
  }

  # ========================================================================
  # VPC CONFIGURATION
  # ========================================================================
  vpc_config = {
    cidr_block           = "10.0.0.0/16"
    enable_dns_hostnames = true
    enable_dns_support   = true
    availability_zones   = ["${local.aws_region}a", "${local.aws_region}b", "${local.aws_region}c"]

    # Public subnets for ALB and future NAT Gateways
    public_subnets = [
      { cidr = "10.0.1.0/24", az = "${local.aws_region}a" },
      { cidr = "10.0.2.0/24", az = "${local.aws_region}b" },
      { cidr = "10.0.3.0/24", az = "${local.aws_region}c" }
    ]

    # Private app subnets for EKS nodes - /20 for VPC CNI IP allocation
    private_app_subnets = [
      { cidr = "10.0.16.0/20", az = "${local.aws_region}a" },
      { cidr = "10.0.32.0/20", az = "${local.aws_region}b" },
      { cidr = "10.0.48.0/20", az = "${local.aws_region}c" }
    ]

    # Private data subnets for RDS and ElastiCache
    private_data_subnets = [
      { cidr = "10.0.64.0/24", az = "${local.aws_region}a" },
      { cidr = "10.0.65.0/24", az = "${local.aws_region}b" },
      { cidr = "10.0.66.0/24", az = "${local.aws_region}c" }
    ]

    # VPC Endpoints to reduce NAT costs
    vpc_endpoints = [
      "sqs",
      "sns",
      "s3",
      "secretsmanager",
      "appconfig",
      "appconfigdata",
      "ecr.api",
      "ecr.dkr"
    ]

    # NAT Gateway configuration - DISABLED (using NAT instance instead)
    enable_nat_gateway = false
    single_nat_gateway = false
  }

  # ========================================================================
  # EC2 CONFIGURATION
  # ========================================================================
  ec2_config = {
    nat = {
      instance_type         = "t4g.nano"  # ARM64 Graviton for $3/month cost
      volume_size           = 8
      volume_type           = "gp3"
      delete_on_termination = true
    }
  }

  # ========================================================================
  # EKS CLUSTER CONFIGURATION
  # ========================================================================
  eks_config = {
    cluster_name    = join("-", [local.environment, local.project_name, "cluster"])
    cluster_version = "1.29"

    endpoint_private_access = true
    endpoint_public_access  = true

    system_node_group = {
      name           = "system"
      instance_types = ["t3.medium"]
      capacity_type  = "ON_DEMAND"
      desired_size   = 2
      min_size       = 2
      max_size       = 3
      disk_size      = 50
      labels = {
        role = "system"
      }
      taints = []
    }

    app_node_group = {
      name           = "application"
      instance_types = ["m6i.large", "m5.large", "m5a.large"]
      capacity_type  = "SPOT"
      desired_size   = 2
      min_size       = 1
      max_size       = 10
      disk_size      = 100
      labels = {
        role = "application"
      }
      taints = []
    }

    ai_node_group = {
      enabled        = true
      name           = "ai-gpu"
      instance_types = ["g4dn.xlarge"]
      capacity_type  = "SPOT"
      desired_size   = 0
      min_size       = 0
      max_size       = 1
      disk_size      = 100
      labels = {
        role                                = "ai"
        "nvidia.com/gpu"                    = "true"
        "node.kubernetes.io/instance-type"  = "g4dn.xlarge"
      }
      taints = [
        {
          key    = "nvidia.com/gpu"
          value  = "true"
          effect = "NO_SCHEDULE"
        }
      ]
    }

    addons = {
      vpc_cni = {
        version = "v1.16.0-eksbuild.1"
        configuration_values = jsonencode({
          enableNetworkPolicy = "true"
          env = {
            ENABLE_PREFIX_DELEGATION = "true"
            WARM_PREFIX_TARGET       = "1"
          }
        })
      }
      coredns = {
        version = "v1.11.1-eksbuild.4"
      }
      kube_proxy = {
        version = "v1.29.0-eksbuild.1"
      }
      ebs_csi_driver = {
        version = "v1.26.1-eksbuild.1"
      }
    }

    cluster_logging            = ["api", "audit", "authenticator", "controllerManager", "scheduler"]
    enable_container_insights  = true
  }

  # ========================================================================
  # RDS MYSQL CONFIGURATION
  # ========================================================================
  rds_config = {
    identifier            = join("-", [local.environment, local.project_name, "db"])
    engine                = "mysql"
    engine_version        = "8.0.35"
    instance_class        = local.environment == "prod" ? "db.m6g.large" : "db.t4g.medium"
    allocated_storage     = 20
    max_allocated_storage = 100
    storage_type          = "gp3"
    storage_encrypted     = true
    multi_az              = local.environment == "prod" ? true : false

    database_name = "llm_judge"
    database_port = local.infrastructure_ports.mysql
    username      = "admin"

    backup_retention_period   = local.environment == "prod" ? 7 : 3
    backup_window             = "03:00-04:00"
    maintenance_window        = "mon:04:00-mon:05:00"
    skip_final_snapshot       = local.environment == "prod" ? false : true
    final_snapshot_identifier = "${local.environment}-${local.project_name}-db-final"

    performance_insights_enabled   = true
    performance_insights_retention = 7

    iam_database_authentication_enabled = true

    parameter_group_family = "mysql8.0"
    parameters = [
      { name = "character_set_server", value = "utf8mb4" },
      { name = "collation_server", value = "utf8mb4_unicode_ci" }
    ]
  }

  # ========================================================================
  # ELASTICACHE REDIS CONFIGURATION (DEPRECATED - kept for reference)
  # ========================================================================
  # Redis has been migrated to Kubernetes. This configuration is kept for
  # potential rollback scenarios but is not actively used.
  redis_config = {
    cluster_id           = join("-", [local.environment, local.project_name, "redis"])
    engine               = "redis"
    engine_version       = "7.1"
    node_type            = local.environment == "prod" ? "cache.m6g.large" : "cache.t4g.medium"
    num_cache_nodes      = 1
    parameter_group_name = "default.redis7"
    port                 = local.infrastructure_ports.redis_cache
    default_ttl_seconds  = 604800  # 7 days

    use_serverless = false
    serverless_config = {
      max_ecpu_per_second = 5000
      max_storage_gb      = 5
    }

    snapshot_retention_limit = local.environment == "prod" ? 5 : 1
    snapshot_window          = "05:00-06:00"
    maintenance_window       = "mon:06:00-mon:07:00"

    at_rest_encryption_enabled = true
    transit_encryption_enabled = true
  }

  # ========================================================================
  # KUBERNETES REDIS CONFIGURATION
  # ========================================================================
  # Redis cache running as a StatefulSet in Kubernetes
  # Cost savings: ~$30-50/month compared to ElastiCache
  redis_k8s_config = {
    image            = "redis:7.1-alpine"
    service_name     = "redis"
    service_dns      = "redis.llm-judge.svc.cluster.local"
    port             = 6379
    default_ttl_seconds = 604800  # 7 days

    resources = {
      requests = {
        cpu    = "100m"
        memory = "256Mi"
      }
      limits = {
        cpu    = "500m"
        memory = "512Mi"
      }
    }

    persistence = {
      enabled          = true
      storage_class    = "gp3"
      access_mode      = "ReadWriteOnce"
      size             = "10Gi"
    }

    config = {
      maxmemory        = "256mb"
      maxmemory_policy = "allkeys-lru"
      save             = "900 1 300 10 60 10000"  # RDB snapshots
      appendonly       = "yes"                    # AOF persistence
      appendfsync      = "everysec"
    }
  }

  # ========================================================================
  # SNS CONFIGURATION
  # ========================================================================
  sns_config = {
    topic_names = ["inference", "judge"]
  }

  # ========================================================================
  # APPCONFIG CONFIGURATION
  # ========================================================================
  appconfig_config = {
    application_name            = join("-", [local.environment, local.project_name, "app"])
    application_description     = "LLM Judge Application Configuration"
    environment_name            = local.environment
    environment_description     = "Environment configuration for ${local.environment}"
    configuration_profile_name  = "runtime-config"
    configuration_profile_description = "Runtime configuration for LLM Judge services"

    # Hosted configuration content (JSON) - merged with dynamic values in Terraform
    configuration_content = {
      aws = {
        region     = local.aws_region
        account_id = local.aws_account_id
      }
      sqs = local.sqs_config.worker_config
      redis = {
        default_ttl_seconds = local.redis_config.default_ttl_seconds
      }
      http_timeouts = local.http_timeouts
      services = {
        redis = {
          host = local.service_names.redis
          port = local.service_ports.redis
        }
        persistence = {
          host = local.service_names.persistence
          port = local.service_ports.persistence
        }
        judge_inference = {
          host = local.service_names.inference
          port = local.service_ports.inference
        }
      }
      health_check = local.health_check
    }

    deployment_strategy = {
      name                           = "${local.environment}-${local.project_name}-all-at-once"
      deployment_duration_in_minutes = 0
      growth_factor                  = 100
      final_bake_time_in_minutes     = 0
      growth_type                    = "LINEAR"
    }
  }

  # ========================================================================
  # SECRETS MANAGER CONFIGURATION
  # ========================================================================
  secrets_config = {
    rds_credentials = {
      name        = "${local.environment}/${local.project_name}/rds/credentials"
      description = "RDS MySQL credentials for LLM Judge"
      secret_data = {
        username = local.rds_config.username
        password = "PLACEHOLDER_GENERATE_RANDOM"
        host     = "PLACEHOLDER_RDS_ENDPOINT"
        port     = local.rds_config.database_port
        database = local.rds_config.database_name
      }
    }
  }

  # ========================================================================
  # IAM ROLES CONFIGURATION
  # ========================================================================
  iam_roles_config = {
    nat_router = {
      assume_role_policy = jsonencode({
        Version = "2012-10-17"
        Statement = [{
          Effect    = "Allow"
          Principal = { Service = "ec2.amazonaws.com" }
          Action    = "sts:AssumeRole"
        }]
      })
      policies = {
        ssm = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
      }
    }

    gateway_service = {
      service_name = local.service_names.gateway
      namespace    = local.namespace
      policies = [{
        effect    = "Allow"
        actions   = ["sns:Publish"]
        resources = ["PLACEHOLDER_INFERENCE_TOPIC_ARN"]
      }]
    }

    inference_service = {
      service_name = local.service_names.inference
      namespace    = local.namespace
      policies = [
        {
          effect    = "Allow"
          actions   = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes", "sqs:ChangeMessageVisibility"]
          resources = ["PLACEHOLDER_INFERENCE_QUEUE_ARN"]
        },
        {
          effect    = "Allow"
          actions   = ["sns:Publish"]
          resources = ["PLACEHOLDER_JUDGE_TOPIC_ARN"]
        }
      ]
    }

    judge_service = {
      service_name = local.service_names.judge
      namespace    = local.namespace
      policies = [{
        effect    = "Allow"
        actions   = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes", "sqs:ChangeMessageVisibility"]
        resources = ["PLACEHOLDER_JUDGE_QUEUE_ARN"]
      }]
    }

    external_secrets_operator = {
      service_name = "external-secrets"
      namespace    = "external-secrets-system"
      policies = [{
        effect    = "Allow"
        actions   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
        resources = ["arn:aws:secretsmanager:${local.aws_region}:${local.aws_account_id}:secret:${local.environment}/${local.project_name}/*"]
      }]
    }
  }

  # ========================================================================
  # ECR CONFIGURATION
  # ========================================================================
  ecr_config = {
    repository_prefix = "${local.aws_account_id}.dkr.ecr.${local.aws_region}.amazonaws.com"
    image_tag         = "v1.0.0"
    repositories = {
      gateway     = "${local.aws_account_id}.dkr.ecr.${local.aws_region}.amazonaws.com/${local.service_names.gateway}"
      redis       = "${local.aws_account_id}.dkr.ecr.${local.aws_region}.amazonaws.com/${local.service_names.redis}"
      persistence = "${local.aws_account_id}.dkr.ecr.${local.aws_region}.amazonaws.com/${local.service_names.persistence}"
      inference   = "${local.aws_account_id}.dkr.ecr.${local.aws_region}.amazonaws.com/${local.service_names.inference}"
      judge       = "${local.aws_account_id}.dkr.ecr.${local.aws_region}.amazonaws.com/${local.service_names.judge}"
    }
  }

  # ========================================================================
  # API GATEWAY CONFIGURATION
  # ========================================================================
  api_gateway_config = {
    name          = join("-", [local.environment, local.project_name, "api"])
    description   = "HTTP API Gateway for LLM Judge"
    protocol_type = "HTTP"

    cors_configuration = {
      allow_origins = ["*"]
      allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
      allow_headers = ["Content-Type", "Authorization", "X-Request-ID"]
      max_age       = 300
    }

    throttle_settings = {
      burst_limit = 1000
      rate_limit  = 500
    }

    routes = [
      { path = "/submit", method = "POST", target_port = local.service_ports.gateway },
      { path = "/metadata/{request_id}", method = "GET", target_port = local.service_ports.gateway },
      { path = "/health", method = "GET", target_port = local.service_ports.gateway }
    ]
  }

  # ========================================================================
  # BUDGETS CONFIGURATION
  # ========================================================================
  budgets_config = {
    alert_email = "amit618@gmail.com"
    thresholds  = [50, 100, 150, 200]
  }

  # ========================================================================
  # COMMON TAGS
  # ========================================================================
  common_tags = {
    Project     = local.project_name
    Environment = local.environment
    ManagedBy   = "terraform"
    Region      = local.aws_region
  }
}
