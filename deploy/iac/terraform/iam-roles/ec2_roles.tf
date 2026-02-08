# ========================================================================
# IAM ROLES FOR EC2 INSTANCES
# ========================================================================

locals {
  # Flatten the EC2 IAM policies map for easier iteration
  flattened_ec2_iam_policies = merge([
    for role, policies in var.ec2_iam_policies : {
      for policy_name, policy_arn in policies :
      "${role}.${policy_name}" => {
        role        = role
        policy_name = policy_name
        policy_arn  = policy_arn
      }
    }
  ]...)
}

# ========================================================================
# EC2 IAM SERVICE ROLES
# ========================================================================
resource "aws_iam_role" "ec2_service_roles" {
  for_each           = var.ec2_iam_policies
  name               = join("-", [var.environment, each.key, "service-role"])
  assume_role_policy = var.ec2_assume_role_policy_document

  tags = merge(
    var.common_tags,
    {
      Name = join("-", [var.environment, each.key, "service-role"])
    }
  )
}

# ========================================================================
# EC2 IAM INSTANCE PROFILES
# ========================================================================
resource "aws_iam_instance_profile" "ec2_instance_profiles" {
  for_each = var.ec2_iam_policies
  name     = join("-", [var.environment, each.key, "instance-profile"])
  role     = aws_iam_role.ec2_service_roles[each.key].name

  tags = merge(
    var.common_tags,
    {
      Name = join("-", [var.environment, each.key, "instance-profile"])
    }
  )
}

# ========================================================================
# ATTACH POLICIES TO EC2 ROLES
# ========================================================================
resource "aws_iam_role_policy_attachment" "ec2_policy_attachments" {
  for_each   = local.flattened_ec2_iam_policies
  role       = aws_iam_role.ec2_service_roles[each.value["role"]].name
  policy_arn = each.value["policy_arn"]
}
