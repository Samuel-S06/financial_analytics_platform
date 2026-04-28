# Outputs make it easy to grab key values after `terraform apply` without
# digging through state. Useful in scripts and for confirming what got created.

output "namespace" {
  description = "The namespace created for the application."
  value       = kubernetes_namespace.app.metadata[0].name
}

output "ingress_controller_installed" {
  description = "Whether Terraform installed ingress-nginx (false means we're relying on the Minikube addon)."
  value       = var.install_ingress_nginx
}

output "next_steps" {
  description = "Reminder of what to do after `terraform apply`."
  value       = "Namespace ready. Now run `make deploy` from the project root to install the Helm chart."
}
