output "nat_router_instance" {
  description = "NAT router instance details"
  value = {
    id                = aws_instance.nat_routers.id
    private_ip        = aws_instance.nat_routers.private_ip
    public_ip         = aws_eip.nat_elastic_ips.public_ip
    availability_zone = aws_instance.nat_routers.availability_zone
  }
}

output "nat_elastic_ip" {
  description = "Elastic IP for NAT router"
  value = {
    id         = aws_eip.nat_elastic_ips.id
    public_ip  = aws_eip.nat_elastic_ips.public_ip
    allocation_id = aws_eip.nat_elastic_ips.allocation_id
  }
}
