"""
Shared pytest fixtures.

Provides a TestClient against the FastAPI app for endpoint tests, with any
external dependencies (Redis, etc.) replaced by fakes.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """A FastAPI TestClient that hits the in-process app directly."""
    return TestClient(app)