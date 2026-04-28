# financial_analytics_platform# Financial Analytics Platform

A scalable web platform for financial transaction analysis and savings-goal simulation, built as a final project for a DevOps course. The application itself (FastAPI + React + Redis) is intentionally simple — the focus is on the **DevOps surface around it**: containerization, Kubernetes orchestration via Helm, infrastructure-as-code with Terraform, and CI/CD via GitHub Actions.

## What this project demonstrates

| Topic | How it shows up here |
|---|---|
| **Containerization** | Multi-stage Dockerfiles for both services. Backend runs as a non-root user; frontend is built by Node and served by nginx. |
| **Kubernetes** | A Helm chart deploys frontend, backend, and Redis. Backend uses an HPA for autoscaling. Probes are wired to dedicated `/health` and `/ready` endpoints. Ingress routes `/api/*` to the backend and everything else to the frontend under one hostname. |
| **Infrastructure as Code** | Terraform provisions cluster-level resources (namespace, optional ingress controller). The boundary between Terraform and Helm is explicit — Terraform owns infrastructure, Helm owns the application. |
| **CI/CD** | Two GitHub Actions workflows. CI runs lint + tests + image builds on every PR. Deploy builds and pushes versioned images to GHCR on merge to main, then runs a smoke test against an ephemeral `kind` cluster. |
| **Reproducibility** | `make up` brings up the entire stack on any machine with Minikube installed. |
| **Testability** | pytest suite for backend logic; same tests run locally and in CI. |
| **Observability** | Structured JSON logging from the backend; liveness/readiness probes give Kubernetes accurate signal about pod health. |

## Architecture

```
                  ┌──────────────────┐
                  │  ingress-nginx   │
                  └────────┬─────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
     /api/*   ▼                /*       ▼
        ┌──────────┐            ┌────────────┐
        │ backend  │            │  frontend  │
        │ (FastAPI)│            │  (nginx +  │
        │  ×2 pods │            │   React)   │
        └────┬─────┘            └────────────┘
             │
             ▼
        ┌──────────┐
        │  redis   │  (StatefulSet, persistent)
        │  ×1 pod  │
        └──────────┘
```

## Repository layout

```
financial-platform/
├── Makefile                    One-page tour of all common workflows
├── .github/workflows/          CI (lint/test/build) and Deploy (push/smoke)
├── terraform/                  Cluster-level resources (namespace, ingress)
├── helm/financial-platform/    The application chart
│   ├── Chart.yaml
│   ├── values.yaml             All tunable knobs in one place
│   └── templates/              Deployments, Services, HPA, StatefulSet, Ingress
├── backend/                    FastAPI app + Dockerfile + tests
└── frontend/                   React + Vite app + nginx + Dockerfile
```

## Quickstart

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Minikube](https://minikube.sigs.k8s.io/docs/start/)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [Helm](https://helm.sh/docs/intro/install/)
- [Terraform](https://developer.hashicorp.com/terraform/install) ≥ 1.5

### Bring it up

```bash
# Start Minikube with the ingress and metrics-server addons enabled.
make cluster-up

# Initialize Terraform and create the namespace.
make tf-init
make tf-apply

# Build the images (into Minikube's docker daemon, no registry push needed)
# and install the Helm chart.
make deploy
```

Or simply:

```bash
make up   # equivalent to: cluster-up + tf-init + tf-apply + deploy
```

### Access it

Add a hosts entry pointing the configured ingress host at Minikube:

```bash
echo "$(minikube ip) financial.local" | sudo tee -a /etc/hosts
```

Then open <http://financial.local>.

### Verify everything is running

```bash
make status
```

Expected output: 2 backend pods, 1 frontend pod, 1 redis pod, services for each, an ingress, and an HPA targeting the backend.

### Clicking around

The current frontend is a "spine check" UI. It calls `/api/hello` and displays the responding pod's hostname. Clicking **Refresh** repeatedly will rotate between backend pods, demonstrating that the Service is load-balancing correctly.

## Demoing autoscaling

The HPA scales the backend based on CPU. To trigger it:

```bash
# Generate load against /api/hello
kubectl run -i --rm load --image=busybox --restart=Never -- \
  /bin/sh -c "while true; do wget -q -O- http://backend.financial-platform/hello; done"

# Watch the HPA react in another terminal
kubectl get hpa -n financial-platform -w
```

Pods should scale up from 2 to as many as 6 within a minute or two.

## Manual scale demo

```bash
REPLICAS=4 make scale-backend
make status   # see 4 backend pods
```

## Running tests

```bash
make test    # pytest
make lint    # ruff
```

The same commands run in CI on every PR.

## Tear it down

```bash
make down    # uninstall chart + destroy Terraform + stop Minikube
```

## Implementation notes

### Why Helm and not raw `kubectl apply`?

The chart isn't strictly necessary at this scale, but it gives us templated configuration in one place (`values.yaml`), proper release lifecycle (`helm upgrade`, `helm rollback`), and a single command to install or remove the entire app. Raw YAML scales poorly the moment you have more than one environment or want to tune something.

### Why Terraform if Helm could do it?

Terraform's Kubernetes provider can in principle manage everything Helm does, but using both Terraform and Helm to deploy the same Deployment is genuinely redundant. Instead, this project draws a deliberate boundary:

- **Terraform = cluster infrastructure**: the namespace, optional ingress controller install. Things that exist *before* the app and outlive any single deployment.
- **Helm = the application**: anything that gets versioned and deployed alongside code changes.

That mirrors how teams actually use these tools in practice.

### Why a StatefulSet for Redis?

A single-replica Deployment would technically work for our Redis, but StatefulSet is the correct primitive: it guarantees stable pod identity and gives each replica its own PersistentVolumeClaim. If we ever scaled to a Redis cluster with replication, the Service+StatefulSet shape is what we'd need anyway.

### Why structured JSON logging?

In a single-pod local setup, plain text logs are fine. With multiple replicas and any serious log aggregator (Loki, Elasticsearch, CloudWatch), JSON logs are dramatically easier to filter and correlate. It's a small upfront investment that pays off the first time you need to grep across pods.

## Project status

This is the **DevOps spine** — the application has stub endpoints (`/health`, `/ready`, `/hello`) that prove the infrastructure works end-to-end. The real analysis logic (CSV parsing, spending breakdowns, savings simulation) and the corresponding frontend (upload form, charts, simulation parameters) are scoped placeholders, ready to be filled in without changing any infrastructure.