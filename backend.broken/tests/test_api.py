"""
End-to-end tests through the FastAPI TestClient.

These exercise the real request/response cycle including BackgroundTasks,
which run synchronously in TestClient (which is what we want here - we can
poll the job and assert on the final result without sleep loops).
"""

from io import BytesIO

from fastapi.testclient import TestClient


# --- Spine ------------------------------------------------------------------

def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ready(client: TestClient) -> None:
    r = client.get("/ready")
    assert r.status_code == 200


def test_hello(client: TestClient) -> None:
    r = client.get("/hello")
    assert r.status_code == 200
    body = r.json()
    assert "pod_hostname" in body
    assert body["pod_hostname"]


# --- Upload flow ------------------------------------------------------------

def test_upload_and_poll(client: TestClient, sample_csv: bytes) -> None:
    """Upload a CSV, poll the job, verify analysis results come back."""
    r = client.post(
        "/upload",
        files={"file": ("transactions.csv", BytesIO(sample_csv), "text/csv")},
    )
    assert r.status_code == 202
    job_id = r.json()["job_id"]

    # BackgroundTasks finish before the response is returned to the test
    # client, so the job should already be done by the time we poll.
    r = client.get(f"/job/{job_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "done"

    result = body["result"]
    assert result["summary"]["total_spend"] == 920.0
    assert len(result["by_category"]) == 3


def test_upload_rejects_non_csv(client: TestClient) -> None:
    r = client.post(
        "/upload",
        files={"file": ("image.png", BytesIO(b"not a csv"), "image/png")},
    )
    assert r.status_code == 400


def test_upload_handles_bad_csv(client: TestClient) -> None:
    """Bad CSV should result in a job in 'failed' state, not a 5xx."""
    r = client.post(
        "/upload",
        files={"file": ("bad.csv", BytesIO(b"foo,bar\n1,2\n"), "text/csv")},
    )
    assert r.status_code == 202
    job_id = r.json()["job_id"]

    r = client.get(f"/job/{job_id}")
    body = r.json()
    assert body["status"] == "failed"
    assert "missing required columns" in body["error"]


def test_get_unknown_job_returns_404(client: TestClient) -> None:
    r = client.get("/job/does-not-exist")
    assert r.status_code == 404


# --- Simulation flow --------------------------------------------------------

def test_simulate_after_upload(client: TestClient, sample_csv: bytes) -> None:
    """Full happy path: upload, then simulate against the upload's job_id."""
    # Upload
    r = client.post(
        "/upload",
        files={"file": ("transactions.csv", BytesIO(sample_csv), "text/csv")},
    )
    upload_job_id = r.json()["job_id"]

    # Confirm upload finished
    r = client.get(f"/job/{upload_job_id}")
    assert r.json()["status"] == "done"

    # Submit simulation
    r = client.post(
        "/simulate",
        json={
            "analysis_job_id": upload_job_id,
            "goal_amount": 300.0,
            "months": 12,
            "cut_categories": ["Dining", "Transport"],
        },
    )
    assert r.status_code == 202
    sim_job_id = r.json()["job_id"]

    # Poll simulation result
    r = client.get(f"/job/{sim_job_id}")
    body = r.json()
    assert body["status"] == "done"

    result = body["result"]
    assert result["feasible"] is True
    assert result["required_monthly_savings"] == 25.0
    assert len(result["cuts"]) == 2


def test_simulate_rejects_unknown_analysis_id(client: TestClient) -> None:
    r = client.post(
        "/simulate",
        json={
            "analysis_job_id": "nonexistent",
            "goal_amount": 100.0,
            "months": 12,
            "cut_categories": ["Food"],
        },
    )
    assert r.status_code == 404


def test_simulate_validates_inputs(client: TestClient) -> None:
    """Pydantic should reject negative goal, zero months, empty cut list."""
    r = client.post(
        "/simulate",
        json={
            "analysis_job_id": "any",
            "goal_amount": -5.0,
            "months": 12,
            "cut_categories": ["Food"],
        },
    )
    assert r.status_code == 422  # Pydantic validation error