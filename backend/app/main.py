"""
FastAPI application entry point.

Spine-first version: only health, readiness, and a hello endpoint. This is
enough to verify that:
  - the Docker image builds and runs
  - Kubernetes liveness/readiness probes pass
  - the ingress routes /api/* to this service correctly
  - traffic is being load-balanced across multiple replicas (the pod_hostname
    in /api/hello changes between calls)

Real endpoints (/upload, /simulate, /job/{id}) get added once the spine is
verified end-to-end.
"""

import logging
import socket

from fastapi import FastAPI

from app.config import settings
from app.logging_config import configure_logging
from app.models import HealthResponse, HelloResponse

configure_logging()
log = logging.getLogger(__name__)

app = FastAPI(
    title="Financial Analytics Platform - Backend",
    version="0.1.0-stub",
)


@app.on_event("startup")
async def on_startup() -> None:
    """Logged on every pod start - useful for confirming new replicas come up."""
    log.info("backend starting", extra={"service": settings.service_name})


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """
    Liveness probe.

    Kubernetes will restart the pod if this fails. Should only fail when the
    process is genuinely broken - never on transient downstream issues, since
    a restart wouldn't help anyway.
    """
    return HealthResponse(status="ok", service=settings.service_name)


@app.get("/ready", response_model=HealthResponse)
async def ready() -> HealthResponse:
    """
    Readiness probe.

    Kubernetes uses this to decide whether to send traffic to the pod. Once
    Redis is wired in, this will check the Redis connection - a pod that
    can't talk to Redis shouldn't receive requests, but it also shouldn't be
    killed (Redis might just be temporarily unreachable).
    """
    # TODO once Redis is wired in: ping it and return 503 on failure
    return HealthResponse(status="ready", service=settings.service_name)


@app.get("/hello", response_model=HelloResponse)
async def hello() -> HelloResponse:
    """
    Simple endpoint that returns the pod's hostname.

    Useful for demoing in the presentation: hit this endpoint repeatedly and
    watch pod_hostname rotate between replicas, proving the Service is
    load-balancing correctly across the deployment.
    """
    hostname = socket.gethostname()
    log.info("hello called", extra={"pod_hostname": hostname})
    return HelloResponse(
        message="Hello from the financial-platform backend!",
        pod_hostname=hostname,
    )