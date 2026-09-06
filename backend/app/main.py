"""FastAPI application entry point."""

import logging
import socket
from contextlib import asynccontextmanager

import httpx
from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

# Imported as a module, not `from ... import store`: binding the instance at
# import time would freeze whichever store existed then, and swapping it
# later (as the tests do) would silently have no effect.
from app import job_store
from app import rates as rates_service
from app.auth import get_current_user
from app.config import settings
from app.jobs import run_simulation_job, run_upload_job
from app.logging_config import configure_logging
from app.models import (
    HealthResponse,
    HelloResponse,
    JobStatusResponse,
    JobSubmitResponse,
    JobSummary,
    RatesResponse,
    SimulationRequest,
)

configure_logging()
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("backend starting", extra={"service": settings.service_name})
    if not settings.auth_enabled:
        # Every request is attributed to one shared identity in this mode.
        # Fine on a laptop, never in front of real users.
        log.warning(
            "AUTH IS DISABLED - all requests share one user id",
            extra={"dev_user_id": settings.dev_user_id},
        )
    yield
    log.info("backend shutting down")


app = FastAPI(
    title="Spendline - Backend",
    version="0.2.0",
    lifespan=lifespan,
)

# In production the frontend is served same-origin (nginx proxies /api), so
# this is a no-op. It matters when the frontend is deployed separately - e.g.
# a static host talking to the API on another domain - where the browser
# sends a preflight before every non-GET request.
if settings.cors_origin_list or settings.cors_origin_regex:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_origin_regex=settings.cors_origin_regex or None,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service=settings.service_name)


@app.get("/ready", response_model=HealthResponse)
async def ready() -> HealthResponse:
    if isinstance(job_store.store, job_store.RedisJobStore) and not job_store.store.ping():
        raise HTTPException(status_code=503, detail="Redis unreachable")
    return HealthResponse(status="ready", service=settings.service_name)


@app.get("/hello", response_model=HelloResponse)
async def hello() -> HelloResponse:
    return HelloResponse(
        message="Hello from the spendline backend!",
        pod_hostname=socket.gethostname(),
    )


MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_CONTENT_TYPES = (
    "text/csv",
    "application/vnd.ms-excel",
    "application/octet-stream",
)


@app.post("/upload", response_model=JobSubmitResponse, status_code=202)
async def upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
) -> JobSubmitResponse:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        if not (file.filename and file.filename.lower().endswith(".csv")):
            raise HTTPException(
                status_code=400,
                detail=f"Expected a CSV, got {file.content_type}",
            )

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large; max is {MAX_UPLOAD_BYTES}",
        )

    job_id = job_store.store.create(user_id)
    background_tasks.add_task(run_upload_job, job_id, content)
    return JobSubmitResponse(job_id=job_id, status="pending")


@app.post("/simulate", response_model=JobSubmitResponse, status_code=202)
async def simulate(
    req: SimulationRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user),
) -> JobSubmitResponse:
    parent = job_store.store.get(req.analysis_job_id)
    # Someone else's analysis is reported as missing, not forbidden - a 403
    # would confirm the id exists.
    if parent is None or parent.get("user_id") != user_id:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis job {req.analysis_job_id} not found",
        )
    if parent["status"] != "done":
        raise HTTPException(
            status_code=409,
            detail=(
                f"Analysis job {req.analysis_job_id} is not complete "
                f"(status: {parent['status']})."
            ),
        )

    job_id = job_store.store.create(user_id)
    background_tasks.add_task(
        run_simulation_job,
        job_id,
        req.analysis_job_id,
        req.goal_amount,
        req.months,
        req.cut_categories,
    )
    return JobSubmitResponse(job_id=job_id, status="pending")


@app.get("/job/{job_id}", response_model=JobStatusResponse)
async def get_job(
    job_id: str,
    user_id: str = Depends(get_current_user),
) -> JobStatusResponse:
    record = job_store.store.get(job_id)
    if record is None or record.get("user_id") != user_id:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return JobStatusResponse(**record)


@app.get("/jobs", response_model=list[JobSummary])
async def list_jobs(user_id: str = Depends(get_current_user)) -> list[JobSummary]:
    """The caller's own uploads, newest first."""
    records = job_store.store.list_jobs(user_id)
    return [
        JobSummary(
            job_id=r["job_id"],
            status=r["status"],
            created_at=r.get("created_at"),
            total_spend=(r.get("result") or {}).get("summary", {}).get("total_spend"),
        )
        for r in records
        # Simulation jobs share the store but aren't uploads; only analysis
        # results carry a summary.
        if r.get("result") is None or "summary" in (r.get("result") or {})
    ]


@app.get("/rates", response_model=RatesResponse)
async def rates(
    base: str = "USD",
    _user_id: str = Depends(get_current_user),
) -> RatesResponse:
    """Live exchange rates, so totals can be shown in a second currency."""
    try:
        return RatesResponse(**rates_service.get_rates(base.upper()))
    except httpx.HTTPError as exc:
        log.warning("rate lookup failed", extra={"error": type(exc).__name__})
        raise HTTPException(
            status_code=503,
            detail="Exchange rates are unavailable right now.",
        ) from exc
