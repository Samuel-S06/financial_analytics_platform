"""
Pydantic schemas for request/response payloads.

Right now we only have a hello-world response. As the real endpoints are added
(/upload, /simulate, etc.), their request and response shapes will live here so
that the API surface stays type-checked and self-documenting via FastAPI's
auto-generated OpenAPI schema.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from enum import Enum


class TransactionType(str, Enum):
    DEBIT = "debit"
    CREDIT = "credit"


class Transaction(BaseModel):
    date: datetime
    description: str
    amount: float
    type: TransactionType
    category: Optional[str] = None
    balance: Optional[float] = None


class ParsedData(BaseModel):
    transactions: List[Transaction]
    total_transactions: int
    date_range: tuple[datetime, datetime]
    total_credits: float
    total_debits: float
    net_balance: float


class UploadResponse(BaseModel):
    job_id: str
    status: str
    message: str
    data_summary: Optional[ParsedData] = None


class SimulationRequest(BaseModel):
    job_id: str
    months: int = Field(default=12, ge=1, le=60)
    scenarios: List[str] = Field(default=["baseline"])


class SimulationResult(BaseModel):
    month: int
    scenario: str
    projected_balance: float
    confidence_interval: tuple[float, float]
    factors: dict[str, float]


class SimulationResponse(BaseModel):
    job_id: str
    status: str
    results: List[SimulationResult]
    summary: dict[str, float]


class HealthResponse(BaseModel):
    status: str
    service: str


class HelloResponse(BaseModel):
    message: str
    pod_hostname: str  # useful for demoing load balancing across replicas