# ========================================================================
# HELM RELEASES MODULE - TERRAGRUNT WRAPPER
# Dependency Group 6: Helm Deployments
# ========================================================================

include "root" {
  path           = find_in_parent_folders("root.hcl")
  expose         = true
  merge_strategy = "no_merge"
}

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

dependency "vpc" {
  config_path = "../vpc"
  mock_outputs = { vpc_id = "vpc-mock123456" }
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
      content_poller_service = {
        arn  = "arn:aws:iam::123456789012:role/mock-content-poller-service-irsa-role"
        name = "mock-content-poller-service-irsa-role"
      }
      content_processor_service = {
        arn  = "arn:aws:iam::123456789012:role/mock-content-processor-service-irsa-role"
        name = "mock-content-processor-service-irsa-role"
      }
      query_engine_service = {
        arn  = "arn:aws:iam::123456789012:role/mock-query-engine-service-irsa-role"
        name = "mock-query-engine-service-irsa-role"
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

dependency "appconfig" {
  config_path = "../appconfig"
  mock_outputs = {
    appconfig_application = { id = "mock-app-id", arn = "arn:aws:appconfig:us-east-1:123456789012:application/mock-app-id" }
    appconfig_environment = { id = "mock-env-id" }
    appconfig_profile     = { id = "mock-profile-id" }
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

dependency "sqs" {
  config_path = "../sqs"
  mock_outputs = {
    sqs_queues = {
      content_processing = { url = "https://sqs.us-east-1.amazonaws.com/123456789012/mock-content-processing-queue" }
      query_answering    = { url = "https://sqs.us-east-1.amazonaws.com/123456789012/mock-query-answering-queue" }
    }
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

dependency "sns" {
  config_path = "../sns"
  mock_outputs = {
    sns_topics = {
      content_processing = { arn = "arn:aws:sns:us-east-1:123456789012:mock-content-processing-topic" }
      query_answering    = { arn = "arn:aws:sns:us-east-1:123456789012:mock-query-answering-topic" }
    }
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

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

inputs = {
  aws_account_id = include.root.inputs.aws_account_id
  aws_region     = include.root.inputs.aws_region
  environment    = include.root.inputs.environment
  project_name   = include.root.inputs.project_name
  repo_root      = include.root.locals.repo_root

  namespace = include.root.inputs.namespace

  vpc_id = dependency.vpc.outputs.vpc_id

  cluster_name              = dependency.eks.outputs.eks_cluster.name
  cluster_endpoint          = dependency.eks.outputs.eks_cluster.endpoint
  cluster_ca_certificate    = dependency.eks.outputs.eks_cluster.certificate_authority
  cluster_oidc_provider_arn = dependency.eks.outputs.eks_oidc_provider.arn

  iam_role_arns = {
    gateway_service              = dependency.iam_roles.outputs.iam_service_roles["gateway_service"].arn
    content_poller_service       = dependency.iam_roles.outputs.iam_service_roles["content_poller_service"].arn
    content_processor_service    = dependency.iam_roles.outputs.iam_service_roles["content_processor_service"].arn
    query_engine_service         = dependency.iam_roles.outputs.iam_service_roles["query_engine_service"].arn
    external_secrets_operator    = dependency.iam_roles.outputs.iam_service_roles["external_secrets_operator"].arn
    aws_load_balancer_controller = dependency.iam_roles.outputs.iam_service_roles["aws_load_balancer_controller"].arn
    cluster_autoscaler           = dependency.iam_roles.outputs.iam_service_roles["cluster_autoscaler"].arn
  }

  appconfig_ids = {
    application_id = dependency.appconfig.outputs.appconfig_application.id
    environment_id = dependency.appconfig.outputs.appconfig_environment.id
    profile_id     = dependency.appconfig.outputs.appconfig_profile.id
  }

  ecr_repository_prefix = include.root.inputs.ecr_config.repository_prefix
  image_tag             = include.root.inputs.ecr_config.image_tag

  service_names = include.root.inputs.service_names
  service_ports = include.root.inputs.service_ports

  infrastructure_endpoints = {
    redis_cache = {
      host = "redis-master.${include.root.inputs.namespace}.svc.cluster.local"
      port = 6379
    }
  }

  sqs_queue_urls = {
    content_processing = dependency.sqs.outputs.sqs_queues["content_processing"].url
    query_answering    = dependency.sqs.outputs.sqs_queues["query_answering"].url
  }

  sns_topic_arns = {
    content_processing = dependency.sns.outputs.sns_topics["content_processing"].arn
    query_answering    = dependency.sns.outputs.sns_topics["query_answering"].arn
  }

  kafka_config            = include.root.inputs.kafka_config
  kafka_bootstrap_servers = include.root.inputs.kafka_config.bootstrap_servers
  kafka_consumer_groups   = include.root.inputs.kafka_config.consumer_groups
  kafka_topics = {
    content_processing = include.root.inputs.kafka_config.topics.content_processing.name
    query_answering    = include.root.inputs.kafka_config.topics.query_answering.name
  }

  inference_config = include.root.inputs.inference_config

  autoscaling = include.root.inputs.autoscaling
  common_tags = include.root.inputs.common_tags

  observability_config = include.root.inputs.observability_config
}
