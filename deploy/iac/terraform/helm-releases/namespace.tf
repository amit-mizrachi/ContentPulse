# ========================================================================
# HELM RELEASES MODULE - NAMESPACE
# ========================================================================

locals {
  namespace_name = var.namespace
}

resource "kubernetes_namespace" "llm_judge_namespace" {
  metadata {
    name = local.namespace_name

    labels = {
      name               = local.namespace_name
    }
  }
}
