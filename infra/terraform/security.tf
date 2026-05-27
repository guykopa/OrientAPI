# Security group for the app node (k3s + Argo CD + OrientAPI + PostgreSQL)
resource "aws_security_group" "app" {
  name        = "orientops-app-sg"
  description = "Security group for the k3s app node"
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

  ingress {
    description = "OrientAPI metrics NodePort - monitoring node only"
    from_port   = 30090
    to_port     = 30090
    protocol    = "tcp"
    security_groups = [aws_security_group.monitoring.id]
  }

  ingress {
    description = "node-exporter - monitoring node only"
    from_port   = 9100
    to_port     = 9100
    protocol    = "tcp"
    security_groups = [aws_security_group.monitoring.id]
  }

  egress {
    description = "Allow all outbound - package installs, image pulls, cert renewal"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, { Name = "orientops-app-sg" })
}

# Security group for the monitoring node (Prometheus + Grafana)
resource "aws_security_group" "monitoring" {
  name        = "orientops-monitoring-sg"
  description = "Security group for the Prometheus + Grafana monitoring node"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "SSH - operator IP only"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.operator_ip]
  }

  ingress {
    description = "Grafana UI - operator IP only"
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = [var.operator_ip]
  }

  ingress {
    description = "Prometheus UI - operator IP only (debug)"
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = [var.operator_ip]
  }

  egress {
    description = "Allow all outbound - scraping targets, image pulls"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, { Name = "orientops-monitoring-sg" })
}
