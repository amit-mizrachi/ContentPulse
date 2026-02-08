# ========================================================================
# HELM RELEASES COMMONS - SHARED LOCALS
# ========================================================================

locals {
  # Local chart paths using repo_root (absolute path from terragrunt)
  llm_judge_chart_path = "${var.repo_root}/deploy/helm/charts/llm-judge-service"

  # Common labels for all Helm releases
  common_labels = {}
}
