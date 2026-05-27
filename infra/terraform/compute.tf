data "aws_ami" "ubuntu_22_04" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_key_pair" "operator" {
  key_name   = var.key_pair_name
  public_key = file(var.public_key_path)
  tags       = local.tags
}

# App node: k3s (Argo CD + OrientAPI) + PostgreSQL in Docker on host
resource "aws_instance" "app" {
  ami                    = data.aws_ami.ubuntu_22_04.id
  instance_type          = var.app_instance_type
  key_name               = aws_key_pair.operator.key_name
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.app.id]

  root_block_device {
    volume_size           = var.app_volume_size_gb
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  user_data = templatefile("${path.module}/cloud-init-app.yaml.tftpl", {
    postgres_password = var.postgres_password
  })

  user_data_replace_on_change = true

  tags = merge(local.tags, { Name = "orientops-app" })
}

# Monitoring node: Prometheus + Grafana via Docker Compose
resource "aws_instance" "monitoring" {
  ami                    = data.aws_ami.ubuntu_22_04.id
  instance_type          = var.monitoring_instance_type
  key_name               = aws_key_pair.operator.key_name
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.monitoring.id]

  root_block_device {
    volume_size           = var.monitoring_volume_size_gb
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  user_data = templatefile("${path.module}/cloud-init-monitoring.yaml.tftpl", {
    app_private_ip = aws_instance.app.private_ip
  })

  user_data_replace_on_change = true

  tags = merge(local.tags, { Name = "orientops-monitoring" })
}
