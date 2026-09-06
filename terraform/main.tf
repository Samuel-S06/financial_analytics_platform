# -----------------------------------------------------------------------------
# Terraform: cluster-level resources for the Spendline.
#
# Boundary of responsibility:
#   - Terraform owns: the namespace, the ingress controller (ingress-nginx).
#     These are "cluster infrastructure" - things that exist before any app
#     gets deployed.
#   - Helm (run separately) owns: the application itself (frontend, backend,
#     Redis, ingress rules).
#
# Why this split: Terraform managing app deployments would be redundant with
# Helm. But Terraform managing the cluster's bootstrap pieces is a real use
# case - it's how you'd codify "give me a cluster with ingress ready to use".
# -----------------------------------------------------------------------------

terraform {
  required_version = ">= 1.5"
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.30"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.15"
    }
  }
}

# Use the active kubeconfig context. When running against Minikube, this picks
# up the `minikube` context automatically after `minikube start`.
provider "kubernetes" {
  config_path    = var.kubeconfig_path
  config_context = var.kube_context
}

provider "helm" {
  kubernetes {
    config_path    = var.kubeconfig_path
    config_context = var.kube_context
  }
}

# --- Namespace --------------------------------------------------------------
resource "kubernetes_namespace" "app" {
  metadata {
    name = var.namespace
    labels = {
      "app.kubernetes.io/managed-by" = "terraform"
    }
  }
}

# --- Ingress controller -----------------------------------------------------
# On a real cloud cluster we'd install ingress-nginx via Helm here. On
# Minikube, the `ingress` addon already provides one, so this is a no-op
# unless the user explicitly asks for it via the variable.
#
# Kept as a stub so the structure is in place if we ever target a non-Minikube
# cluster.
resource "helm_release" "ingress_nginx" {
  count = var.install_ingress_nginx ? 1 : 0

  name             = "ingress-nginx"
  repository       = "https://kubernetes.github.io/ingress-nginx"
  chart            = "ingress-nginx"
  namespace        = "ingress-nginx"
  create_namespace = true
  version          = "4.11.3"

  # Sensible defaults for a small cluster.
  set {
    name  = "controller.service.type"
    value = "NodePort"
  }
}
