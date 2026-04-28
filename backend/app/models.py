"""Pydantic schemas for API."""

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class HelloResponse(BaseModel):
    message: str
    pod_hostname: str


class JobSubmitResponse(BaseModel):
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    error: str | None = None
    result: dict[str, Any] | None = None


class SimulationRequest(BaseModel):
    analysis_job_id: str = Field(..., description="ID of the upload job")
    goal_amount: float = Field(..., gt=0)
    months: int = Field(..., gt=0, le=120)
    cut_categories: list[str] = Field(..., min_length=1)
