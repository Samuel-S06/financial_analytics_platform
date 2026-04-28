"""
Pydantic schemas for request/response payloads.

Right now we only have a hello-world response. As the real endpoints are added
(/upload, /simulate, etc.), their request and response shapes will live here so
that the API surface stays type-checked and self-documenting via FastAPI's
auto-generated OpenAPI schema.
"""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str


class HelloResponse(BaseModel):
    message: str
    pod_hostname: str  # useful for demoing load balancing across replicas