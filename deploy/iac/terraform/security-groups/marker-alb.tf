# ========================================================================
# MARKER SECURITY GROUP - ALB
# Marker security group for Application Load Balancer (used as source/target in other SG rules)
# ========================================================================

locals {
  marker_alb_sg_name = join("-", [var.environment, "marker-alb-sg"])
}

resource "aws_security_group" "alb" {
  name        = local.marker_alb_sg_name
  description = "Marker security group for Application Load Balancer (used as source/target in other SG rules)"
  vpc_id      = var.vpc_id

  tags = merge(
    local.sg_tags,
    {
      Name = local.marker_alb_sg_name
    }
  )
}
