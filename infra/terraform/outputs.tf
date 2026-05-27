output "app_public_ip" {
  description = "Public IP of the app node (k3s) — use for DNS, SSH, and kubectl"
  value       = aws_instance.app.public_ip
}

output "app_private_ip" {
  description = "Private IP of the app node — used by Prometheus to scrape metrics"
  value       = aws_instance.app.private_ip
}

output "app_ssh_command" {
  description = "SSH command to connect to the app node"
  value       = "ssh ubuntu@${aws_instance.app.public_ip}"
}

output "app_kubeconfig_command" {
  description = "Command to retrieve the kubeconfig from the app node"
  value       = "scp ubuntu@${aws_instance.app.public_ip}:/home/ubuntu/.kube/config ~/.kube/orientops.yaml && sed -i 's/127.0.0.1/${aws_instance.app.public_ip}/g' ~/.kube/orientops.yaml"
}

output "monitoring_public_ip" {
  description = "Public IP of the monitoring node — Grafana is at http://<this_ip>:3000"
  value       = aws_instance.monitoring.public_ip
}

output "monitoring_ssh_command" {
  description = "SSH command to connect to the monitoring node"
  value       = "ssh ubuntu@${aws_instance.monitoring.public_ip}"
}

output "grafana_url" {
  description = "Grafana dashboard URL (admin/orientops)"
  value       = "http://${aws_instance.monitoring.public_ip}:3000"
}
