include "root" {
  path   = find_in_parent_folders("root.hcl")
  expose = true
}

dependency "sns" {
  config_path = "../sns"
  mock_outputs = {
    sns_topics = {
      content_processing = {
        arn  = "arn:aws:sns:us-east-1:123456789012:mock-content-processing-topic"
        id   = "mock-content-processing-topic"
        name = "dev-simple-sport-news-content-processing-topic"
      }
      query_answering = {
        arn  = "arn:aws:sns:us-east-1:123456789012:mock-query-answering-topic"
        id   = "mock-query-answering-topic"
        name = "dev-simple-sport-news-query-answering-topic"
      }
    }
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

dependency "sqs" {
  config_path = "../sqs"
  mock_outputs = {
    sqs_queues = {
      content_processing = {
        arn  = "arn:aws:sqs:us-east-1:123456789012:mock-content-processing-queue"
        id   = "mock-content-processing-queue"
        url  = "https://sqs.us-east-1.amazonaws.com/123456789012/mock-content-processing-queue"
        name = "dev-simple-sport-news-content-processing-queue"
      }
      query_answering = {
        arn  = "arn:aws:sqs:us-east-1:123456789012:mock-query-answering-queue"
        id   = "mock-query-answering-queue"
        url  = "https://sqs.us-east-1.amazonaws.com/123456789012/mock-query-answering-queue"
        name = "dev-simple-sport-news-query-answering-queue"
      }
    }
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

dependency "secrets" {
  config_path = "../secrets"
  mock_outputs = {
    secrets = {
      llm_api_keys = {
        arn  = "arn:aws:secretsmanager:us-east-1:123456789012:secret:mock-llm-api-keys"
        id   = "mock-llm-api-keys"
        name = "dev/simple-sport-news/llm/api-keys"
      }
      mongodb_credentials = {
        arn  = "arn:aws:secretsmanager:us-east-1:123456789012:secret:mock-mongodb-creds"
        id   = "mock-mongodb-creds"
        name = "dev/simple-sport-news/mongodb/credentials"
      }
      reddit_credentials = {
        arn  = "arn:aws:secretsmanager:us-east-1:123456789012:secret:mock-reddit-creds"
        id   = "mock-reddit-creds"
        name = "dev/simple-sport-news/reddit/credentials"
      }
    }
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

dependency "eks" {
  config_path = "../eks"
  mock_outputs = {
    eks_cluster = { name = "mock-cluster" }
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
  aws_account_id = include.root.inputs.aws_account_id
  aws_region     = include.root.inputs.aws_region
  environment    = include.root.inputs.environment
  project_name   = include.root.inputs.project_name

  iam_roles_config = {
    for k, v in include.root.inputs.iam_roles_config : k => v
    if lookup(v, "service_name", null) != null && lookup(v, "namespace", null) != null
  }

  eks_cluster_name      = dependency.eks.outputs.eks_cluster.name
  eks_oidc_provider_arn = dependency.eks.outputs.eks_oidc_provider.arn
  eks_oidc_provider_url = dependency.eks.outputs.eks_oidc_provider.url

  sqs_queue_arns = {
    content_processing = dependency.sqs.outputs.sqs_queues["content_processing"].arn
    query_answering    = dependency.sqs.outputs.sqs_queues["query_answering"].arn
  }

  sns_topic_arns = {
    content_processing = dependency.sns.outputs.sns_topics["content_processing"].arn
    query_answering    = dependency.sns.outputs.sns_topics["query_answering"].arn
  }

  secret_arns = {
    for key, secret in dependency.secrets.outputs.secrets : key => secret.arn
  }

  common_tags = include.root.inputs.common_tags

  ec2_iam_policies = {
    nat-router = include.root.inputs.iam_roles_config.nat_router.policies
  }
  ec2_assume_role_policy_document = include.root.inputs.iam_roles_config.nat_router.assume_role_policy
}
