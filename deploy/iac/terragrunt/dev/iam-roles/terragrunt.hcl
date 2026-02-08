# ========================================================================
# IAM ROLES MODULE - TERRAGRUNT WRAPPER (IRSA for EKS)
# Dependency Group 3: IAM Layer (depends on: sns, sqs, secrets, eks)
# ========================================================================

include "root" {
  path   = find_in_parent_folders("root.hcl")
  expose = true
}

dependency "sns" {
  config_path = "../sns"

  mock_outputs = {
    sns_topics = {
      inference = {
        arn  = "arn:aws:sns:us-east-1:123456789012:mock-inference-topic"
        id   = "mock-inference-topic"
        name = "dev-nadav-inference-topic"
      }
      judge = {
        arn  = "arn:aws:sns:us-east-1:123456789012:mock-judge-topic"
        id   = "mock-judge-topic"
        name = "dev-nadav-judge-topic"
      }
    }
  }

  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

dependency "sqs" {
  config_path = "../sqs"

  mock_outputs = {
    sqs_queues = {
      inference = {
        arn  = "arn:aws:sqs:us-east-1:123456789012:mock-inference-queue"
        id   = "mock-inference-queue"
        url  = "https://sqs.us-east-1.amazonaws.com/123456789012/mock-inference-queue"
        name = "dev-nadav-inference-queue"
      }
      judge = {
        arn  = "arn:aws:sqs:us-east-1:123456789012:mock-judge-queue"
        id   = "mock-judge-queue"
        url  = "https://sqs.us-east-1.amazonaws.com/123456789012/mock-judge-queue"
        name = "dev-nadav-judge-queue"
      }
    }
  }

  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

dependency "secrets" {
  config_path = "../secrets"

  # Note: Only RDS credentials are stored in Secrets Manager.
  # LLM API keys (OpenAI, Google) are provided per-request by users (BYOK model).
  mock_outputs = {
    secrets = {
      rds_credentials = {
        arn  = "arn:aws:secretsmanager:us-east-1:123456789012:secret:mock-rds-creds"
        id   = "mock-rds-creds"
        name = "dev/nadav/llm-judge/rds/credentials"
      }
    }
  }

  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

dependency "eks" {
  config_path = "../eks"

  mock_outputs = {
    eks_cluster = {
      name = "mock-cluster"
    }
    eks_oidc_provider = {
      arn = "arn:aws:iam::123456789012:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/MOCK123456"
      url = "https://oidc.eks.us-east-1.amazonaws.com/id/MOCK123456"
    }
  }

  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

terraform {
  source = "${include.root.locals.repo_root}/deploy/iac/terraform/iam-roles"
}

inputs = {
  # Core variables
  aws_account_id = include.root.inputs.aws_account_id
  aws_region     = include.root.inputs.aws_region
  environment    = include.root.inputs.environment
  project_name   = include.root.inputs.project_name

  # IAM roles configuration (IRSA only - filter out EC2 roles like nat_router)
  iam_roles_config = {
    for k, v in include.root.inputs.iam_roles_config : k => v
    if lookup(v, "service_name", null) != null && lookup(v, "namespace", null) != null
  }

  # Dependencies - direct references to dependency outputs
  eks_cluster_name      = dependency.eks.outputs.eks_cluster.name
  eks_oidc_provider_arn = dependency.eks.outputs.eks_oidc_provider.arn
  eks_oidc_provider_url = dependency.eks.outputs.eks_oidc_provider.url

  sqs_queue_arns = {
    inference = dependency.sqs.outputs.sqs_queues["inference"].arn
    judge     = dependency.sqs.outputs.sqs_queues["judge"].arn
  }

  sns_topic_arns = {
    inference = dependency.sns.outputs.sns_topics["inference"].arn
    judge     = dependency.sns.outputs.sns_topics["judge"].arn
  }

  # Only RDS credentials - LLM API keys are user-provided per-request (BYOK)
  secret_arns = {
    rds_credentials = dependency.secrets.outputs.secrets.rds_credentials.arn
  }

  # Common tags
  common_tags = include.root.inputs.common_tags

  # ========================================================================
  # EC2 IAM ROLES CONFIGURATION
  # ========================================================================
  # EC2 policies map: role_name -> {policy_name: policy_arn}
  ec2_iam_policies = {
    nat-router = include.root.inputs.iam_roles_config.nat_router.policies
  }

  # Assume role policy for EC2
  ec2_assume_role_policy_document = include.root.inputs.iam_roles_config.nat_router.assume_role_policy
}
