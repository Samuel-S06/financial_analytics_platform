# Financial Analytics Platform

A web app for analyzing personal transaction data and simulating savings goals, deployed on Kubernetes. 

## What it does

Upload a CSV of bank transactions and get:
- A spending breakdown by category and over time
- A savings simulation: pick a goal, timeframe, and categories to cut from, and get back recommended monthly budgets and feasibility

## Tools used

- **Docker** — containerizes the backend and frontend
- **Kubernetes (Minikube)** — runs the services, load-balances traffic, restarts failures
- **Helm** — templates and deploys all Kubernetes resources as one chart
- **Terraform** — provisions the namespace and cluster-level resources as code
- **GitHub Actions** — lints, tests, and builds images on every push
- **Redis** — shared store for job state and parsed data, keeping backend pods stateless
- **FastAPI / React** — the application itself

## What I accomplished

A working end-to-end deployment with multi-stage Docker builds, a Helm chart with autoscaling and proper probes, Terraform-managed infrastructure, a CI/CD pipeline, async job processing backed by Redis, and a React frontend with charts and live polling.

## Code documentation

DevOps configuration lives in three places, each documented inline:

- **`helm/financial-platform/templates/`** — Kubernetes manifests for the deployments, services, ingress, autoscaler, and Redis StatefulSet. Comments explain probe configuration, the rationale for each resource, and the rewrite rules in the ingress.
- **`terraform/`** — provisions cluster-level resources. Comments explain the boundary between what Terraform owns vs. what Helm owns.
- **`.github/workflows/`** — CI and deploy pipelines. Comments explain the job structure and caching strategy.

The `Makefile` at the project root documents and exposes every common workflow (`make up`, `make deploy`, `make test`, etc.).

## How to test and view it

### Prerequisites
Docker, Minikube, kubectl, Helm, Terraform.

### Bring it up

```bash
make up
echo "127.0.0.1 financial.local" | sudo tee -a /etc/hosts
minikube tunnel   # leave running in a separate terminal
```

Visit <http://financial.local>.

### Try It!

Drag the included `sample_transactions.csv` onto the upload zone. Charts appear, then submit a simulation (e.g. goal $600, 12 months, cut from Dining and Entertainment) to see recommended budgets.

### Other commands

```bash
make test      # run the pytest suite
make lint      # run ruff
make status    # show all running pods, services, ingress, and HPA
make down      # tear everything down
```