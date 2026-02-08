# ========================================================================
# INGRESS - HTTPS/HTTP FROM WORLD TO ALB
# ========================================================================

# Ingress: HTTPS from internet
resource "aws_vpc_security_group_ingress_rule" "alb_https" {
  security_group_id = aws_security_group.alb.id
  description       = "Allow HTTPS from internet"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
  cidr_ipv4         = "0.0.0.0/0"

  tags = merge(
    local.sg_tags,
    {
      Name = "alb-https-ingress"
    }
  )
}

# Ingress: HTTP from internet (for redirect to HTTPS)
resource "aws_vpc_security_group_ingress_rule" "alb_http" {
  security_group_id = aws_security_group.alb.id
  description       = "Allow HTTP from internet (redirect to HTTPS)"
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"
  cidr_ipv4         = "0.0.0.0/0"

  tags = merge(
    local.sg_tags,
    {
      Name = "alb-http-ingress"
    }
  )
}
