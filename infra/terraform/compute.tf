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

resource "aws_instance" "k3s" {
  ami                    = data.aws_ami.ubuntu_22_04.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.operator.key_name
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.k3s.id]

  root_block_device {
    volume_size           = var.root_volume_size_gb
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  user_data = file("${path.module}/cloud-init.yaml")

  # Allow cloud-init (k3s + Argo CD install) to complete before marking healthy
  user_data_replace_on_change = true

  tags = merge(local.tags, { Name = "orientops-k3s-node" })
}
