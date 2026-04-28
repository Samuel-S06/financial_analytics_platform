variable "kubeconfig_path" {
  description = "Path to the kubeconfig file. Defaults to ~/.kube/config."
  type        = string
  default     = "~/.kube/config"
}

variable "kube_context" {
  description = "Kubernetes context to use. For Minikube this is 'minikube'."
  type        = string
  default     = "minikube"
}

variable "namespace" {
  description = "Namespace to create for the application."
  type        = string
  default     = "financial-platform"
}

variable "install_ingress_nginx" {
  description = "Whether to install ingress-nginx via Helm. Leave false on Minikube (use the addon instead)."
  type        = bool
  default     = false
}
