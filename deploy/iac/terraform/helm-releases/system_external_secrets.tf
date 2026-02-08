# ========================================================================
# SYSTEM - EXTERNAL SECRETS OPERATOR
# AWS Secrets Manager integration for Kubernetes secrets
# ========================================================================

resource "helm_release" "external_secrets_release" {
  name       = "external-secrets"
  repository = "https://charts.external-secrets.io"
  chart      = "external-secrets"
  namespace  = "external-secrets-system"
  version    = "0.9.11"

  create_namespace = true

  set {
    name  = "serviceAccount.create"
    value = "true"
  }

  set {
    name  = "serviceAccount.name"
    value = "external-secrets"
  }

  set {
    name  = "serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
    value = var.iam_role_arns["external_secrets_operator"]
  }

  set {
    name  = "installCRDs"
    value = "true"
  }

  depends_on = [
    helm_release.metrics_server_release
  ]
}
