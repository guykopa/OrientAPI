variable "aws_region" {
  description = "AWS region to deploy into — eu-west-3 (Paris) for RGPD compliance"
  type        = string
  default     = "eu-west-3"
}

variable "app_instance_type" {
  description = "EC2 instance type for the app node (k3s + Argo CD + OrientAPI + PostgreSQL in Docker)"
  type        = string
  default     = "t3.small"
}

variable "monitoring_instance_type" {
  description = "EC2 instance type for the monitoring node (Prometheus + Grafana via Docker Compose)"
  type        = string
  default     = "t3.micro"
}

variable "operator_ip" {
  description = "Operator's public IP in CIDR notation — SSH and management UIs are restricted to this IP"
  type        = string
}

variable "key_pair_name" {
  description = "Name of the AWS key pair to create for SSH access to both instances"
  type        = string
  default     = "orientops-key"
}

variable "public_key_path" {
  description = "Local path to the SSH public key file uploaded to AWS"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "app_volume_size_gb" {
  description = "Root EBS volume size for the app node in GiB — fits k3s images, logs, and Postgres data"
  type        = number
  default     = 20
}

variable "monitoring_volume_size_gb" {
  description = "Root EBS volume size for the monitoring node in GiB — fits Prometheus and Grafana data"
  type        = number
  default     = 15
}

variable "postgres_password" {
  description = "Password for the PostgreSQL orientapi user — injected into cloud-init, never committed"
  type        = string
  sensitive   = true
}
