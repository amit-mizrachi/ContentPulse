# ========================================================================
# HELM RELEASES MODULE - EXTERNAL SECRETS CLUSTER SECRET STORE
# ========================================================================

locals {
  secret_store_name = "aws-secrets-manager"
}

resource "kubernetes_manifest" "cluster_secret_store" {
  manifest = {
    apiVersion = "external-secrets.io/v1beta1"
    kind       = "ClusterSecretStore"
    metadata = {
      name = local.secret_store_name
    }
    spec = {
      provider = {
        aws = {
          service = "SecretsManager"
          region  = var.aws_region
          auth = {
            jwt = {
              serviceAccountRef = {
                name      = "external-secrets"
                namespace = "external-secrets-system"
              }
            }
          }
        }
      }
    }
  }

  depends_on = [
    helm_release.external_secrets_release
  ]
}
