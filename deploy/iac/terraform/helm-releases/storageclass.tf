# ========================================================================
# HELM RELEASES MODULE - STORAGE CLASS
# ========================================================================
# AWS EBS gp3 volumes for Redis persistence
# ========================================================================

resource "kubernetes_storage_class" "gp3" {
  metadata {
    name = "gp3"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "false"
    }
    labels = {
      "app.kubernetes.io/managed-by" = "terraform"
      "app.kubernetes.io/part-of"    = var.project_name
    }
  }

  storage_provisioner    = "ebs.csi.aws.com"
  volume_binding_mode    = "WaitForFirstConsumer"
  allow_volume_expansion = true
  reclaim_policy         = "Delete"

  parameters = {
    type      = "gp3"
    encrypted = "true"
    # gp3 defaults: 3000 IOPS, 125 MB/s throughput
    # Can be increased if needed:
    # iops       = "3000"
    # throughput = "125"
  }
}
