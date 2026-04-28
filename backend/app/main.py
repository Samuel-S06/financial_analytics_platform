"""FastAPI application entry point."""

import logging
import socket
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile

from app.config import settings
from app.job_store import RedisJobStore, store
from app.jobs import run_simulation_job, run_upload_job
from app.logging_config import configure_logging
from app.models import (
    HealthResponse,
    HelloResponse,
    JobStatusResponse,
    JobSubmitResponse,
    SimulationRequest,
)

configure_logging()
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("backend starting", extra={"service": settings.service_name})
    yield
    log.info("backend shutting down")


app = FastAPI(
    title="Financial Analytics Platform - Backend",
    version="0.2.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service=settings.service_name)


@app.get("/ready", response_model=HealthResponse)
async def ready() -> HealthResponse:
    if isinstance(store, RedisJobStore) and not store.ping():
        raise HTTPException(status_code=503, detail="Redis unreachable")
    return HealthResponse(status="ready", service=settings.service_name)


@app.get("/hello", response_model=HelloResponse)
async def hello() -> HelloResponse:
    return HelloResponse(
        message="Hello from the financial-platform backend!",
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

    job_id = store.create()
    background_tasks.add_task(run_upload_job, job_id, content)
    return JobSubmitResponse(job_id=job_id, status="pending")


@app.post("/simulate", response_model=JobSubmitResponse, status_code=202)
async def simulate(
    req: SimulationRequest,
    background_tasks: BackgroundTasks,
) -> JobSubmitResponse:
    parent = store.get(req.analysis_job_id)
    if parent is None:
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

    job_id = store.create()
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
async def get_job(job_id: str) -> JobStatusResponse:
    record = store.get(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return JobStatusResponse(**record)
