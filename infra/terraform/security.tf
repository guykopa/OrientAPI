resource "aws_security_group" "k3s" {
  name        = "orientops-k3s-sg"
  description = "Security group for the k3s single-node cluster"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "SSH - operator IP only"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.operator_ip]
  }

  ingress {
    description = "HTTP - Traefik ingress, redirects to HTTPS"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS - Traefik ingress"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Kubernetes API - operator IP only"
    from_port   = 6443
    to_port     = 6443
    protocol    = "tcp"
    cidr_blocks = [var.operator_ip]
  }

  ingress {
    description = "Argo CD UI - NodePort, operator IP only"
    from_port   = 30443
    to_port     = 30443
    protocol    = "tcp"
    cidr_blocks = [var.operator_ip]
  }

  egress {
    description = "Allow all outbound - package installs, image pulls, cert renewal"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, { Name = "orientops-k3s-sg" })
}
