"""Shared pytest fixtures."""

from app import config

config.settings.use_redis = False

from app import job_store  # noqa: E402

job_store.store = job_store.InMemoryJobStore()

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    job_store.store = job_store.InMemoryJobStore()
    return TestClient(app)


@pytest.fixture
def sample_csv() -> bytes:
    return b"""date,category,amount,description
2024-01-05,Groceries,150.00,Trader Joe's
2024-01-10,Dining,80.00,Restaurant
2024-01-15,Transport,30.00,Subway
2024-02-03,Groceries,200.00,Whole Foods
2024-02-08,Dining,120.00,Sushi
2024-02-20,Transport,40.00,Uber
2024-03-04,Groceries,175.00,Costco
2024-03-12,Dining,90.00,Pizza
2024-03-25,Transport,35.00,Train
"""


@pytest.fixture
def messy_csv() -> bytes:
    return b"""date,category,amount
2024-01-05,Groceries,100.00
not-a-date,Dining,50.00
2024-01-10,,30.00
2024-01-15,Transport,not-a-number
2024-01-20,Transport,25.00
"""


@pytest.fixture
def malformed_csv() -> bytes:
    return b"""foo,bar,baz
1,2,3
"""
