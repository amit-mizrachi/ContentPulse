# ========================================================================
# IRSA COMMONS - SHARED LOCALS AND CONFIGURATION
# ========================================================================

locals {
  # Common tags for all IAM resources
  iam_tags = var.common_tags

  # OIDC provider URL without https:// prefix (used in trust policies)
  oidc_provider_id = var.eks_oidc_provider_url != "" ? replace(var.eks_oidc_provider_url, "https://", "") : ""

  # Flag to determine if IRSA resources should be created
  create_irsa = var.eks_oidc_provider_arn != ""
}
