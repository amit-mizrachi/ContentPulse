# ========================================================================
# HELM RELEASES MODULE - TERRAGRUNT WRAPPER
# Dependency Group 6: Helm Deployments (depends on: eks, iam-roles, secrets, appconfig, rds, sqs, sns)
# ========================================================================

include "root" {
  path           = find_in_parent_folders("root.hcl")
  expose         = true
  merge_strategy = "no_merge"
}

# ========================================================================
# REMOTE STATE (copied from root since we use no_merge)
# ========================================================================
remote_state {
  backend = "s3"

  generate = {
    path      = "backend.tf"
    if_exists = "overwrite_terragrunt"
  }

  config = {
    bucket       = "${include.root.locals.environment}-${include.root.locals.project_name}-terraform-state"
    key          = "dev/helm-releases/terraform.tfstate"
    region       = include.root.locals.aws_region
    encrypt      = true
    use_lockfile = true
  }
}

# ========================================================================
# TERRAFORM SETTINGS (copied from root since we use no_merge)
# ========================================================================

# ========================================================================
# PROVIDERS (AWS + Helm + Kubernetes)
# ========================================================================
generate "aws_provider" {
  path      = "aws_provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
terraform {
  required_version = ">= 1.10.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.25"
    }
  }
}

provider "aws" {
  region = "${include.root.locals.aws_region}"

  default_tags {
    tags = {
      Project     = "${include.root.locals.project_name}"
      Environment = "${include.root.locals.environment}"
      ManagedBy   = "terraform"
    }
  }
}
EOF
}

# ========================================================================
# DEPENDENCIES
# ========================================================================

dependency "vpc" {
  config_path = "../vpc"

  mock_outputs = {
    vpc_id = "vpc-mock123456"
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

dependency "eks" {
  config_path = "../eks"

  mock_outputs = {
    eks_cluster = {
      name                  = "mock-cluster"
      endpoint              = "https://mock-eks-endpoint.eks.us-east-1.amazonaws.com"
      certificate_authority = base64encode("mock-ca-cert")
    }
    eks_oidc_provider = {
      arn = "arn:aws:iam::123456789012:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/MOCK123456"
      url = "https://oidc.eks.us-east-1.amazonaws.com/id/MOCK123456"
    }
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

dependency "iam_roles" {
  config_path = "../iam-roles"

  mock_outputs = {
    iam_service_roles = {
      gateway_service = {
        arn  = "arn:aws:iam::123456789012:role/mock-gateway-service-irsa-role"
        name = "mock-gateway-service-irsa-role"
      }
      redis_service = {
        arn  = "arn:aws:iam::123456789012:role/mock-redis-service-irsa-role"
        name = "mock-redis-service-irsa-role"
      }
      persistence_service = {
        arn  = "arn:aws:iam::123456789012:role/mock-persistence-service-irsa-role"
        name = "mock-persistence-service-irsa-role"
      }
      inference_service = {
        arn  = "arn:aws:iam::123456789012:role/mock-inference-service-irsa-role"
        name = "mock-inference-service-irsa-role"
      }
      judge_service = {
        arn  = "arn:aws:iam::123456789012:role/mock-judge-service-irsa-role"
        name = "mock-judge-service-irsa-role"
      }
      external_secrets_operator = {
        arn  = "arn:aws:iam::123456789012:role/mock-external-secrets-irsa-role"
        name = "mock-external-secrets-irsa-role"
      }
      aws_load_balancer_controller = {
        arn  = "arn:aws:iam::123456789012:role/mock-aws-load-balancer-controller-irsa-role"
        name = "mock-aws-load-balancer-controller-irsa-role"
      }
      cluster_autoscaler = {
        arn  = "arn:aws:iam::123456789012:role/mock-cluster-autoscaler-irsa-role"
        name = "mock-cluster-autoscaler-irsa-role"
      }
    }
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

dependency "secrets" {
  config_path = "../secrets"

  mock_outputs = {
    secrets = {
      rds_credentials = {
        arn  = "arn:aws:secretsmanager:us-east-1:123456789012:secret:mock-rds-creds"
        name = "dev/llm-judge/rds/credentials"
      }
    }
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

dependency "appconfig" {
  config_path = "../appconfig"

  mock_outputs = {
    appconfig_application = {
      id  = "mock-app-id"
      arn = "arn:aws:appconfig:us-east-1:123456789012:application/mock-app-id"
    }
    appconfig_environment = {
      id = "mock-env-id"
    }
    appconfig_profile = {
      id = "mock-profile-id"
    }
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

# NOTE: Redis runs in-cluster (deployed by this module) instead of ElastiCache for cost savings

dependency "rds" {
  config_path = "../rds"

  mock_outputs = {
    db_instance = {
      address = "mock-rds.us-east-1.rds.amazonaws.com"
      port    = 3306
    }
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

dependency "sqs" {
  config_path = "../sqs"

  mock_outputs = {
    sqs_queues = {
      inference = {
        url = "https://sqs.us-east-1.amazonaws.com/123456789012/mock-inference-queue"
      }
      judge = {
        url = "https://sqs.us-east-1.amazonaws.com/123456789012/mock-judge-queue"
      }
    }
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

dependency "sns" {
  config_path = "../sns"

  mock_outputs = {
    sns_topics = {
      inference = {
        arn = "arn:aws:sns:us-east-1:123456789012:mock-inference-topic"
      }
      judge = {
        arn = "arn:aws:sns:us-east-1:123456789012:mock-judge-topic"
      }
    }
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

# ========================================================================
# TERRAFORM SOURCE AND SETTINGS
# ========================================================================

terraform {
  source = "${include.root.locals.repo_root}/deploy/iac/terraform/helm-releases"

  extra_arguments "retry_lock" {
    commands  = ["init", "apply", "refresh", "import", "plan", "taint", "untaint"]
    arguments = ["-lock-timeout=20m"]
  }

  extra_arguments "disable_input" {
    commands  = get_terraform_commands_that_need_input()
    arguments = ["-input=false"]
  }
}

# ========================================================================
# INPUTS
# ========================================================================

inputs = {
  # Core variables
  aws_account_id = include.root.inputs.aws_account_id
  aws_region     = include.root.inputs.aws_region
  environment    = include.root.inputs.environment
  project_name   = include.root.inputs.project_name
  repo_root      = include.root.locals.repo_root

  # Kubernetes namespace
  namespace = include.root.inputs.namespace

  # VPC configuration from dependency
  vpc_id = dependency.vpc.outputs.vpc_id

  # EKS cluster details from dependency
  cluster_name           = dependency.eks.outputs.eks_cluster.name
  cluster_endpoint       = dependency.eks.outputs.eks_cluster.endpoint
  cluster_ca_certificate = dependency.eks.outputs.eks_cluster.certificate_authority
  cluster_oidc_provider_arn = dependency.eks.outputs.eks_oidc_provider.arn

  # IAM roles from dependency
  iam_role_arns = {
    gateway_service              = dependency.iam_roles.outputs.iam_service_roles["gateway_service"].arn
    redis_service                = dependency.iam_roles.outputs.iam_service_roles["redis_service"].arn
    persistence_service          = dependency.iam_roles.outputs.iam_service_roles["persistence_service"].arn
    inference_service            = dependency.iam_roles.outputs.iam_service_roles["inference_service"].arn
    judge_service                = dependency.iam_roles.outputs.iam_service_roles["judge_service"].arn
    external_secrets_operator    = dependency.iam_roles.outputs.iam_service_roles["external_secrets_operator"].arn
    aws_load_balancer_controller = dependency.iam_roles.outputs.iam_service_roles["aws_load_balancer_controller"].arn
    cluster_autoscaler           = dependency.iam_roles.outputs.iam_service_roles["cluster_autoscaler"].arn
  }

  # Secrets configuration from dependency
  secrets_config = {
    rds_credentials = {
      name = dependency.secrets.outputs.secrets.rds_credentials.name
      arn  = dependency.secrets.outputs.secrets.rds_credentials.arn
    }
  }

  # AppConfig IDs from dependency
  appconfig_ids = {
    application_id = dependency.appconfig.outputs.appconfig_application.id
    environment_id = dependency.appconfig.outputs.appconfig_environment.id
    profile_id     = dependency.appconfig.outputs.appconfig_profile.id
  }

  # ECR configuration from configuration.hcl
  ecr_repository_prefix = include.root.inputs.ecr_config.repository_prefix
  image_tag             = include.root.inputs.ecr_config.image_tag

  # Service configuration from configuration.hcl
  service_names = include.root.inputs.service_names
  service_ports = include.root.inputs.service_ports

  # Infrastructure endpoints from dependencies
  infrastructure_endpoints = {
    # Redis runs in-cluster - endpoint configured in helm values
    redis_cache = {
      host = "redis-master.${include.root.inputs.namespace}.svc.cluster.local"
      port = 6379
    }
    rds = {
      host = dependency.rds.outputs.db_instance.address
      port = dependency.rds.outputs.db_instance.port
    }
  }

  # SQS queue URLs from dependency
  sqs_queue_urls = {
    inference = dependency.sqs.outputs.sqs_queues["inference"].url
    judge     = dependency.sqs.outputs.sqs_queues["judge"].url
  }

  # SNS topic ARNs from dependency
  sns_topic_arns = {
    inference = dependency.sns.outputs.sns_topics["inference"].arn
    judge     = dependency.sns.outputs.sns_topics["judge"].arn
  }

  # Autoscaling configuration from configuration.hcl
  autoscaling = include.root.inputs.autoscaling

  # Common tags
  common_tags = include.root.inputs.common_tags
}
