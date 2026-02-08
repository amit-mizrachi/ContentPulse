# ========================================================================
# SECURITY GROUPS MODULE - COMMONS
# Shared locals and data sources for security groups
# ========================================================================

locals {
  sg_tags = merge(
    var.common_tags,
    {
    }
  )

  # Cluster name for Kubernetes tags
  cluster_name = join("-", [var.environment, var.project_name, "cluster"])
}
