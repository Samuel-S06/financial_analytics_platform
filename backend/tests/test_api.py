"""End-to-end API tests."""

from io import BytesIO

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200


def test_ready(client: TestClient) -> None:
    r = client.get("/ready")
    assert r.status_code == 200


def test_hello(client: TestClient) -> None:
    r = client.get("/hello")
    assert r.status_code == 200
    assert "pod_hostname" in r.json()


def test_upload_and_poll(client: TestClient, sample_csv: bytes) -> None:
    r = client.post(
        "/upload",
        files={"file": ("transactions.csv", BytesIO(sample_csv), "text/csv")},
    )
    assert r.status_code == 202
    job_id = r.json()["job_id"]

    r = client.get(f"/job/{job_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "done"
    assert body["result"]["summary"]["total_spend"] == 920.0


def test_upload_rejects_non_csv(client: TestClient) -> None:
    r = client.post(
        "/upload",
        files={"file": ("image.png", BytesIO(b"not csv"), "image/png")},
    )
    assert r.status_code == 400


def test_unknown_job_404(client: TestClient) -> None:
    r = client.get("/job/does-not-exist")
    assert r.status_code == 404


def test_simulate_after_upload(client: TestClient, sample_csv: bytes) -> None:
    r = client.post(
        "/upload",
        files={"file": ("t.csv", BytesIO(sample_csv), "text/csv")},
    )
    upload_id = r.json()["job_id"]

    r = client.post(
        "/simulate",
        json={
            "analysis_job_id": upload_id,
            "goal_amount": 300.0,
            "months": 12,
            "cut_categories": ["Dining", "Transport"],
        },
    )
    assert r.status_code == 202
    sim_id = r.json()["job_id"]

    r = client.get(f"/job/{sim_id}")
    body = r.json()
    assert body["status"] == "done"
    assert body["result"]["feasible"] is True


def test_simulate_unknown_analysis(client: TestClient) -> None:
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
