# ========================================================================
# HELM RELEASES MODULE - NAMESPACE
# ========================================================================

locals {
  namespace_name = var.namespace
}

resource "kubernetes_namespace" "simple_sport_news_namespace" {
  metadata {
    name = local.namespace_name

    labels = {
      name               = local.namespace_name
    }
  }
}
