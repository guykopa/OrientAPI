output "instance_public_ip" {
  description = "Public IP of the k3s node — use this in your DNS or for direct access"
  value       = aws_instance.k3s.public_ip
}

output "instance_public_dns" {
  description = "Public DNS hostname of the k3s node"
  value       = aws_instance.k3s.public_dns
}

output "ssh_command" {
  description = "SSH command to connect to the node"
  value       = "ssh ubuntu@${aws_instance.k3s.public_ip}"
}

output "kubeconfig_command" {
  description = "Command to retrieve the kubeconfig from the node"
  value       = "scp ubuntu@${aws_instance.k3s.public_ip}:/etc/rancher/k3s/k3s.yaml ~/.kube/orientops.yaml && sed -i 's/127.0.0.1/${aws_instance.k3s.public_ip}/g' ~/.kube/orientops.yaml"
}
