# ========================================================================
# HELM RELEASES COMMONS - SHARED LOCALS
# ========================================================================

locals {
  # Local chart paths using repo_root (absolute path from terragrunt)
  simple_sport_news_chart_path = "${var.repo_root}/deploy/helm/charts/simple-sport-news-service"

  # Common labels for all Helm releases
  common_labels = {}
}
