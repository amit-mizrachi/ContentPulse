# ========================================================================
# SIMPLE_SPORT_NEWS - GLOBAL CONFIGURATION
# Single Source of Truth for simple_sport_news Infrastructure
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
  project_name       = "simple-sport-news"
  namespace          = "simple-sport-news" # Kubernetes namespace

  # ========================================================================
  # SERVICE PORTS - SINGLE SOURCE OF TRUTH
  # ========================================================================
  service_ports = {
    gateway           = 8000
    content_poller    = 8005
    content_processor = 8003
    query_engine      = 8004
  }

  # ========================================================================
  # INFRASTRUCTURE PORTS
  # ========================================================================
  infrastructure_ports = {
    redis_cache = 6379
    mongodb     = 27017
    kafka       = 9092
    dns         = 53
    https       = 443
    http        = 80
  }

  # ========================================================================
  # SERVICE NAMES - SINGLE SOURCE OF TRUTH
  # ========================================================================
  service_names = {
    gateway           = "gateway-service"
    content_poller    = "content-poller-service"
    content_processor = "content-processor-service"
    query_engine      = "query-engine-service"
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
    inference_client = 120.0
  }

  # ========================================================================
  # SQS CONFIGURATION - COMPLETE
  # ========================================================================
  sqs_config = {
    queue_names = {
      content_processing = "content-processing"
      query_answering    = "query-answering"
    }

    queue_subscriptions = {
      content_processing = ["content_processing"]
      query_answering    = ["query_answering"]
    }

    queue_properties = {
      delay_seconds             = 0
      max_message_size          = 262144   # 256 KB
      message_retention_seconds = 1209600  # 14 days
      receive_wait_time_seconds = 20       # Long polling
    }

    queue_visibility_timeout_seconds = {
      content_processing = 300
      query_answering    = 300
    }

    queue_max_receive_count = {
      content_processing = 3
      query_answering    = 3
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
  # KAFKA CONFIGURATION
  # ========================================================================
  kafka_config = {
    # Strimzi Kafka Operator
    strimzi = {
      operator_version  = "0.43.0"
      operator_namespace = "strimzi-system"
    }

    # Kafka cluster deployed via Strimzi CRD
    cluster = {
      name     = "simple-sport-news-kafka"
      version  = "3.8.0"
      replicas = 1                # Single broker for dev (3 for prod)

      resources = {
        requests = {
          cpu    = "500m"
          memory = "1Gi"
        }
        limits = {
          cpu    = "1000m"
          memory = "2Gi"
        }
      }

      storage = {
        type = "persistent-claim"
        size = "20Gi"
        storage_class = "gp3"
        delete_claim  = true  # Delete PVC when cluster is deleted (dev only)
      }

      listeners = {
        plain = {
          port = 9092
          type = "internal"
          tls  = false
        }
      }
    }

    # Kafka topics
    topics = {
      content_processing = {
        name       = "content-processing"
        partitions = 3
        replicas   = 1  # Must be <= broker count
        config = {
          "retention.ms"  = "604800000"  # 7 days
          "cleanup.policy" = "delete"
        }
      }
      query_answering = {
        name       = "query-answering"
        partitions = 3
        replicas   = 1
        config = {
          "retention.ms"  = "604800000"  # 7 days
          "cleanup.policy" = "delete"
        }
      }
    }

    # Kafka consumer groups (for KEDA scaling)
    consumer_groups = {
      content_processor = "content-processor-group"
      query_engine      = "query-engine-group"
    }

    # Bootstrap server DNS (Strimzi convention)
    bootstrap_servers = "simple-sport-news-kafka-kafka-bootstrap.simple-sport-news.svc.cluster.local:9092"
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
      content_poller = {
        min_replicas = 1
        max_replicas = 3
      }
      content_processor = {
        min_replicas = 2
        max_replicas = 20
      }
      query_engine = {
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

    # Private data subnets for managed data services
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
      instance_type         = "t4g.micro"  # Upgraded from nano for LLM API traffic
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
    public_access_cidrs     = ["0.0.0.0/0"]  # TODO: Restrict to your VPN/office IP (e.g., ["203.0.113.0/24"])

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
      enabled        = false  # Disabled by default — enable for local inference
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
  # INFERENCE CONFIGURATION
  # ========================================================================
  inference_config = {
    content_processor = {
      inference_mode = "remote"       # "remote" | "local"
      provider_type  = "google"       # "openai" | "google" | "ollama"
      model          = "gemini-2.0-flash"
      api_key_secret = "llm-api-keys"
      gpu_resources  = { enabled = false, nvidia_gpu_count = 1 }
    }
    query_engine = {
      inference_mode = "remote"
      provider_type  = "google"
      model          = "gemini-2.0-flash"
      api_key_secret = "llm-api-keys"
      gpu_resources  = { enabled = false, nvidia_gpu_count = 0 }
    }
  }

  # ========================================================================
  # MONGODB CONFIGURATION (replaces RDS)
  # ========================================================================
  mongodb_config = {
    connection_string_secret = "mongodb-atlas-credentials"
    database_name            = "simple-sport-news"
    collections = {
      articles = "articles"
      queries  = "queries"
    }
  }

  # ========================================================================
  # KUBERNETES REDIS CONFIGURATION
  # ========================================================================
  redis_k8s_config = {
    image            = "redis:7.1-alpine"
    service_name     = "redis"
    service_dns      = "redis.simple-sport-news.svc.cluster.local"
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
      save             = "900 1 300 10 60 10000"
      appendonly       = "yes"
      appendfsync      = "everysec"
    }
  }

  # ========================================================================
  # OBSERVABILITY CONFIGURATION (Grafana Alloy + Grafana Cloud)
  # ========================================================================
  observability_config = {
    namespace = "observability-system"

    # Grafana Alloy Helm chart
    alloy = {
      chart_version = "0.12.0"
    }

    # kube-state-metrics for cluster-level K8s metrics
    kube_state_metrics = {
      chart_version = "5.25.1"
    }

    # Grafana Cloud authentication
    # Populate these with your Grafana Cloud instance details
    grafana_cloud = {
      instance_id = ""  # Your Grafana Cloud instance ID (numeric)
      api_key     = ""  # Your Grafana Cloud API key (token)
    }

    # Backend endpoints (Grafana Cloud)
    # Replace XXX with your Grafana Cloud stack region slug
    endpoints = {
      loki_url                    = "https://logs-prod-XXX.grafana.net/loki/api/v1/push"
      tempo_endpoint              = "tempo-XXX.grafana.net:443"
      prometheus_remote_write_url = "https://prometheus-prod-XXX.grafana.net/api/prom/push"
    }

    # Alloy DaemonSet resources (logs + node metrics collector, runs on every node)
    daemonset_resources = {
      requests = { cpu = "100m", memory = "256Mi" }
      limits   = { cpu = "500m", memory = "512Mi" }
    }

    # Alloy Deployment resources (trace receiver, 2 replicas on system nodes)
    deployment_resources = {
      requests = { cpu = "100m", memory = "256Mi" }
      limits   = { cpu = "500m", memory = "512Mi" }
    }
  }

  # ========================================================================
  # SNS CONFIGURATION
  # ========================================================================
  sns_config = {
    topic_names = ["content_processing", "query_answering"]
  }

  # ========================================================================
  # APPCONFIG CONFIGURATION
  # ========================================================================
  appconfig_config = {
    application_name            = join("-", [local.environment, local.project_name, "app"])
    application_description     = "simple_sport_news Application Configuration"
    environment_name            = local.environment
    environment_description     = "Environment configuration for ${local.environment}"
    configuration_profile_name  = "runtime-config"
    configuration_profile_description = "Runtime configuration for simple_sport_news services"

    # Hosted configuration content (JSON) - merged with dynamic values in Terraform
    configuration_content = {
      aws = {
        region     = local.aws_region
        account_id = local.aws_account_id
      }
      sqs = local.sqs_config.worker_config
      kafka = {
        bootstrap_servers = local.kafka_config.bootstrap_servers
        consumer_groups   = local.kafka_config.consumer_groups
        topics = {
          content_processing = local.kafka_config.topics.content_processing.name
          query_answering    = local.kafka_config.topics.query_answering.name
        }
      }
      mongodb = {
        database_name = local.mongodb_config.database_name
        collections   = local.mongodb_config.collections
      }
      inference = {
        content_processor = {
          provider_type = local.inference_config.content_processor.provider_type
          model         = local.inference_config.content_processor.model
          mode          = local.inference_config.content_processor.inference_mode
        }
        query_engine = {
          provider_type = local.inference_config.query_engine.provider_type
          model         = local.inference_config.query_engine.model
          mode          = local.inference_config.query_engine.inference_mode
        }
      }
      redis = {
        default_ttl_seconds = local.redis_k8s_config.default_ttl_seconds
      }
      observability = {
        traces = {
          collector = {
            endpoint = "http://alloy-traces.${local.observability_config.namespace}.svc.cluster.local:4318/v1/traces"
          }
          sample_rate              = 1.0     # 100% for dev, reduce for prod
          tracer_flush_timeout_ms  = 30000
        }
      }
      http_timeouts = local.http_timeouts
      health_check  = local.health_check
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
    llm_api_keys = {
      name        = "${local.environment}/${local.project_name}/llm/api-keys"
      description = "LLM provider API keys (Google, OpenAI)"
    }
    mongodb_credentials = {
      name        = "${local.environment}/${local.project_name}/mongodb/credentials"
      description = "MongoDB Atlas connection credentials"
    }
    reddit_credentials = {
      name        = "${local.environment}/${local.project_name}/reddit/credentials"
      description = "Reddit API credentials for content polling"
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
        resources = ["PLACEHOLDER_QUERY_ANSWERING_TOPIC_ARN"]
      }]
    }

    content_poller_service = {
      service_name = local.service_names.content_poller
      namespace    = local.namespace
      policies = [{
        effect    = "Allow"
        actions   = ["sns:Publish"]
        resources = ["PLACEHOLDER_CONTENT_PROCESSING_TOPIC_ARN"]
      }]
    }

    content_processor_service = {
      service_name = local.service_names.content_processor
      namespace    = local.namespace
      policies = [
        {
          effect    = "Allow"
          actions   = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes", "sqs:ChangeMessageVisibility"]
          resources = ["PLACEHOLDER_CONTENT_PROCESSING_QUEUE_ARN"]
        },
        {
          effect    = "Allow"
          actions   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
          resources = ["arn:aws:secretsmanager:${local.aws_region}:${local.aws_account_id}:secret:${local.environment}/${local.project_name}/llm/*"]
        }
      ]
    }

    query_engine_service = {
      service_name = local.service_names.query_engine
      namespace    = local.namespace
      policies = [
        {
          effect    = "Allow"
          actions   = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes", "sqs:ChangeMessageVisibility"]
          resources = ["PLACEHOLDER_QUERY_ANSWERING_QUEUE_ARN"]
        },
        {
          effect    = "Allow"
          actions   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
          resources = ["arn:aws:secretsmanager:${local.aws_region}:${local.aws_account_id}:secret:${local.environment}/${local.project_name}/llm/*"]
        }
      ]
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
      base              = "${local.aws_account_id}.dkr.ecr.${local.aws_region}.amazonaws.com/${local.project_name}/base"
      gateway           = "${local.aws_account_id}.dkr.ecr.${local.aws_region}.amazonaws.com/${local.service_names.gateway}"
      content_poller    = "${local.aws_account_id}.dkr.ecr.${local.aws_region}.amazonaws.com/${local.service_names.content_poller}"
      inference         = "${local.aws_account_id}.dkr.ecr.${local.aws_region}.amazonaws.com/inference-service"
    }
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
