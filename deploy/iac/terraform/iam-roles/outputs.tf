# ========================================================================
# IAM ROLES MODULE - OUTPUTS
# ========================================================================

# ========================================================================
# IRSA ROLES OUTPUTS
# ========================================================================
output "iam_service_roles" {
  description = "IAM roles for service accounts (IRSA)"
  value = local.create_irsa ? {
    gateway_service = {
      arn  = aws_iam_role.gateway_service_irsa[0].arn
      id   = aws_iam_role.gateway_service_irsa[0].id
      name = aws_iam_role.gateway_service_irsa[0].name
    }
    redis_service = {
      arn  = aws_iam_role.redis_service_irsa[0].arn
      id   = aws_iam_role.redis_service_irsa[0].id
      name = aws_iam_role.redis_service_irsa[0].name
    }
    persistence_service = {
      arn  = aws_iam_role.persistence_service_irsa[0].arn
      id   = aws_iam_role.persistence_service_irsa[0].id
      name = aws_iam_role.persistence_service_irsa[0].name
    }
    inference_service = {
      arn  = aws_iam_role.inference_service_irsa[0].arn
      id   = aws_iam_role.inference_service_irsa[0].id
      name = aws_iam_role.inference_service_irsa[0].name
    }
    judge_service = {
      arn  = aws_iam_role.judge_service_irsa[0].arn
      id   = aws_iam_role.judge_service_irsa[0].id
      name = aws_iam_role.judge_service_irsa[0].name
    }
    external_secrets_operator = {
      arn  = aws_iam_role.external_secrets_irsa[0].arn
      id   = aws_iam_role.external_secrets_irsa[0].id
      name = aws_iam_role.external_secrets_irsa[0].name
    }
    aws_load_balancer_controller = {
      arn  = aws_iam_role.alb_controller_irsa[0].arn
      id   = aws_iam_role.alb_controller_irsa[0].id
      name = aws_iam_role.alb_controller_irsa[0].name
    }
    cluster_autoscaler = {
      arn  = aws_iam_role.cluster_autoscaler_irsa[0].arn
      id   = aws_iam_role.cluster_autoscaler_irsa[0].id
      name = aws_iam_role.cluster_autoscaler_irsa[0].name
    }
  } : {}
}

output "iam_service_policies" {
  description = "IAM policies for service accounts"
  value = local.create_irsa ? {
    gateway_service = {
      arn  = aws_iam_policy.gateway_service_policy[0].arn
      id   = aws_iam_policy.gateway_service_policy[0].id
      name = aws_iam_policy.gateway_service_policy[0].name
    }
    redis_service = {
      arn  = aws_iam_policy.redis_service_policy[0].arn
      id   = aws_iam_policy.redis_service_policy[0].id
      name = aws_iam_policy.redis_service_policy[0].name
    }
    persistence_service = {
      arn  = aws_iam_policy.persistence_service_policy[0].arn
      id   = aws_iam_policy.persistence_service_policy[0].id
      name = aws_iam_policy.persistence_service_policy[0].name
    }
    inference_service = {
      arn  = aws_iam_policy.inference_service_policy[0].arn
      id   = aws_iam_policy.inference_service_policy[0].id
      name = aws_iam_policy.inference_service_policy[0].name
    }
    judge_service = {
      arn  = aws_iam_policy.judge_service_policy[0].arn
      id   = aws_iam_policy.judge_service_policy[0].id
      name = aws_iam_policy.judge_service_policy[0].name
    }
    external_secrets_operator = {
      arn  = aws_iam_policy.external_secrets_policy[0].arn
      id   = aws_iam_policy.external_secrets_policy[0].id
      name = aws_iam_policy.external_secrets_policy[0].name
    }
    aws_load_balancer_controller = {
      arn  = aws_iam_policy.alb_controller_policy[0].arn
      id   = aws_iam_policy.alb_controller_policy[0].id
      name = aws_iam_policy.alb_controller_policy[0].name
    }
    cluster_autoscaler = {
      arn  = aws_iam_policy.cluster_autoscaler_policy[0].arn
      id   = aws_iam_policy.cluster_autoscaler_policy[0].id
      name = aws_iam_policy.cluster_autoscaler_policy[0].name
    }
  } : {}
}

# Kubernetes service account annotations (for Helm values)
output "service_account_annotations" {
  description = "Annotations for Kubernetes service accounts"
  value = local.create_irsa ? {
    gateway_service = {
      "eks.amazonaws.com/role-arn" = aws_iam_role.gateway_service_irsa[0].arn
    }
    redis_service = {
      "eks.amazonaws.com/role-arn" = aws_iam_role.redis_service_irsa[0].arn
    }
    persistence_service = {
      "eks.amazonaws.com/role-arn" = aws_iam_role.persistence_service_irsa[0].arn
    }
    inference_service = {
      "eks.amazonaws.com/role-arn" = aws_iam_role.inference_service_irsa[0].arn
    }
    judge_service = {
      "eks.amazonaws.com/role-arn" = aws_iam_role.judge_service_irsa[0].arn
    }
    external_secrets_operator = {
      "eks.amazonaws.com/role-arn" = aws_iam_role.external_secrets_irsa[0].arn
    }
    aws_load_balancer_controller = {
      "eks.amazonaws.com/role-arn" = aws_iam_role.alb_controller_irsa[0].arn
    }
    cluster_autoscaler = {
      "eks.amazonaws.com/role-arn" = aws_iam_role.cluster_autoscaler_irsa[0].arn
    }
  } : {}
}

# ========================================================================
# EC2 IAM ROLES OUTPUTS
# ========================================================================
output "ec2_iam_service_roles" {
  description = "Map of EC2 IAM service roles with standardized output structure"
  value = {
    for key, role in aws_iam_role.ec2_service_roles : key => {
      arn  = role.arn
      id   = role.id
      name = role.name
    }
  }
}

output "ec2_iam_instance_profiles" {
  description = "Map of EC2 IAM instance profiles with standardized output structure"
  value = {
    for key, profile in aws_iam_instance_profile.ec2_instance_profiles : key => {
      arn  = profile.arn
      id   = profile.id
      name = profile.name
    }
  }
}
