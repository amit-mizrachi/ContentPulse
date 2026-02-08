# ========================================================================
# INGRESS - ALL TRAFFIC FROM ALB TO EKS NODES
# ========================================================================

locals {
  ingress_all_from_alb_to_eks_group_name = join("-", [var.environment, "ingress-all-from-alb-to-eks-sg"])
}

resource "aws_security_group" "ingress_all_from_alb_to_eks" {
  name        = local.ingress_all_from_alb_to_eks_group_name
  description = "Allow all inbound traffic from ALB to EKS nodes"
  vpc_id      = var.vpc_id

  tags = merge(
    local.sg_tags,
    {
      Name = local.ingress_all_from_alb_to_eks_group_name
    }
  )
}

# Ingress: All traffic from ALB
resource "aws_vpc_security_group_ingress_rule" "eks_nodes_from_alb" {
  security_group_id            = aws_security_group.eks_nodes.id
  description                  = "Allow all traffic from ALB"
  ip_protocol                  = "-1"
  referenced_security_group_id = aws_security_group.alb.id

  tags = merge(
    local.sg_tags,
    {
      Name = "eks-nodes-from-alb-ingress"
    }
  )
}

# Ingress: Node-to-node communication
resource "aws_vpc_security_group_ingress_rule" "eks_nodes_internal" {
  security_group_id            = aws_security_group.eks_nodes.id
  description                  = "Allow node-to-node communication"
  ip_protocol                  = "-1"
  referenced_security_group_id = aws_security_group.eks_nodes.id

  tags = merge(
    local.sg_tags,
    {
      Name = "eks-nodes-internal-ingress"
    }
  )
}

# Ingress: From EKS Control Plane (HTTPS)
resource "aws_vpc_security_group_ingress_rule" "eks_nodes_from_control_plane" {
  security_group_id = aws_security_group.eks_nodes.id
  description       = "Allow traffic from EKS control plane"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
  cidr_ipv4         = var.vpc_cidr_block

  tags = merge(
    local.sg_tags,
    {
      Name = "eks-nodes-from-control-plane-ingress"
    }
  )
}

# Ingress: Kubelet API from Control Plane
resource "aws_vpc_security_group_ingress_rule" "eks_nodes_kubelet" {
  security_group_id = aws_security_group.eks_nodes.id
  description       = "Allow kubelet API from control plane"
  from_port         = 10250
  to_port           = 10250
  ip_protocol       = "tcp"
  cidr_ipv4         = var.vpc_cidr_block

  tags = merge(
    local.sg_tags,
    {
      Name = "eks-nodes-kubelet-ingress"
    }
  )
}
