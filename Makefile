# Financial Analytics Platform - Makefile
# A single entry point for all common workflows. Run `make help` to see options.

# Variables ---------------------------------------------------------------
BACKEND_IMAGE := financial-platform/backend
FRONTEND_IMAGE := financial-platform/frontend
TAG := dev
NAMESPACE := financial-platform
HELM_RELEASE := financial-platform
HELM_CHART := ./helm/financial-platform

# Use Minikube's docker daemon so images are available to the cluster
# without needing to push to a registry. Equivalent to `eval $(minikube docker-env)`.
MINIKUBE_DOCKER_ENV := eval $$(minikube docker-env) &&

.PHONY: help
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- Cluster lifecycle ---------------------------------------------------

.PHONY: cluster-up
cluster-up: ## Start Minikube with the ingress addon enabled
	# Memory is in MB. Must be <= Docker Desktop's allocated memory.
	# Bump Docker Desktop -> Settings -> Resources -> Memory if you hit limits.
	minikube start --cpus=4 --memory=3800
	minikube addons enable ingress
	minikube addons enable metrics-server  # required for HPA

.PHONY: cluster-down
cluster-down: ## Stop Minikube
	minikube stop

.PHONY: cluster-destroy
cluster-destroy: ## Delete the Minikube cluster entirely
	minikube delete

# --- Build ---------------------------------------------------------------

.PHONY: build
build: build-backend build-frontend ## Build both Docker images into Minikube's daemon

.PHONY: build-backend
build-backend: ## Build the backend image
	$(MINIKUBE_DOCKER_ENV) docker build -t $(BACKEND_IMAGE):$(TAG) ./backend

.PHONY: build-frontend
build-frontend: ## Build the frontend image
	$(MINIKUBE_DOCKER_ENV) docker build -t $(FRONTEND_IMAGE):$(TAG) ./frontend

# --- Infrastructure ------------------------------------------------------

.PHONY: tf-init
tf-init: ## Initialize Terraform (run once after cluster-up)
	cd terraform && terraform init

.PHONY: tf-apply
tf-apply: ## Apply Terraform: namespace, ingress-nginx, cert-manager
	cd terraform && terraform apply -auto-approve

.PHONY: tf-destroy
tf-destroy: ## Tear down Terraform-managed resources
	cd terraform && terraform destroy -auto-approve

# --- Deploy --------------------------------------------------------------

.PHONY: deploy
deploy: build ## Build images and deploy via Helm
	helm upgrade --install $(HELM_RELEASE) $(HELM_CHART) \
		--namespace $(NAMESPACE) \
		--set backend.image.tag=$(TAG) \
		--set frontend.image.tag=$(TAG)

.PHONY: undeploy
undeploy: ## Uninstall the Helm release
	helm uninstall $(HELM_RELEASE) --namespace $(NAMESPACE)

.PHONY: status
status: ## Show pods, services, and ingress in our namespace
	kubectl get pods,svc,ingress,hpa -n $(NAMESPACE)

# --- Test ----------------------------------------------------------------

.PHONY: test
test: ## Run the backend test suite locally (no container)
	cd backend && python -m pytest -v

.PHONY: lint
lint: ## Lint the backend with ruff
	cd backend && ruff check app/ tests/

# --- Convenience ---------------------------------------------------------

.PHONY: up
up: cluster-up tf-init tf-apply deploy ## Full bring-up: cluster + infra + app

.PHONY: down
down: undeploy tf-destroy cluster-down ## Full tear-down

.PHONY: logs-backend
logs-backend: ## Tail backend logs
	kubectl logs -n $(NAMESPACE) -l app=backend -f --tail=100

.PHONY: scale-backend
scale-backend: ## Manually scale backend (REPLICAS=N make scale-backend)
	kubectl scale deployment -n $(NAMESPACE) backend --replicas=$${REPLICAS:-3}