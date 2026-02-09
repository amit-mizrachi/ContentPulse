include "root" {
  path   = find_in_parent_folders("root.hcl")
  expose = true
}

terraform {
  source = "${include.root.locals.repo_root}/deploy/iac/terraform/ecr"
}

inputs = {
  aws_account_id   = include.root.inputs.aws_account_id
  aws_region       = include.root.inputs.aws_region
  environment      = include.root.inputs.environment
  project_name     = include.root.inputs.project_name
  repository_names = [
    "base",
    "gateway-service",
    "content-poller-service",
    "inference-service"
  ]
  common_tags = include.root.inputs.common_tags
}
