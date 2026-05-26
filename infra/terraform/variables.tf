variable "aws_region" {
  description = "AWS region to deploy into — eu-west-3 (Paris) for RGPD compliance"
  type        = string
  default     = "eu-west-3"
}

variable "instance_type" {
  description = "EC2 instance type — t3.small provides 2 GiB RAM needed for the full stack"
  type        = string
  default     = "t3.small"
}

variable "operator_ip" {
  description = "Operator's public IP in CIDR notation — SSH is restricted to this IP only"
  type        = string
}

variable "key_pair_name" {
  description = "Name of the AWS key pair to create for SSH access"
  type        = string
  default     = "orientops-key"
}

variable "public_key_path" {
  description = "Local path to the SSH public key file uploaded to AWS"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "root_volume_size_gb" {
  description = "Size of the root EBS volume in GiB — 20 GiB fits k3s + images + logs"
  type        = number
  default     = 20
}
