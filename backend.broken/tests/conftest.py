"""
Shared pytest fixtures.

Forces the in-memory job store for all tests via early monkeypatching, so the
test suite doesn't need a running Redis instance.
"""

import pytest

# Force in-memory store BEFORE importing the app, since job_store.py picks
# the backend at import time based on settings.use_redis.
from app import config

config.settings.use_redis = False

from app import job_store  # noqa: E402

job_store.store = job_store.InMemoryJobStore()

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    """A FastAPI TestClient that hits the in-process app directly."""
    # Reset the store between tests so order doesn't matter.
    job_store.store = job_store.InMemoryJobStore()
    return TestClient(app)


@pytest.fixture
def sample_csv() -> bytes:
    """
    Well-formed CSV covering 3 categories across 3 months.

    Spending totals:
      Groceries:     150 + 200 + 175 = 525
      Dining:         80 + 120 +  90 = 290
      Transport:      30 +  40 +  35 = 105

    Total: 920 over 3 months = 306.67/month average.
    """
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
    """CSV with rows that should be dropped (bad date, bad amount, empty cat)."""
    return b"""date,category,amount
2024-01-05,Groceries,100.00
not-a-date,Dining,50.00
2024-01-10,,30.00
2024-01-15,Transport,not-a-number
2024-01-20,Transport,25.00
"""


@pytest.fixture
def malformed_csv() -> bytes:
    """CSV missing required columns - should fail to parse entirely."""
    return b"""foo,bar,baz
1,2,3
"""