"""Smoke tests for the spine endpoints. More tests get added with real logic."""

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "service" in body


def test_ready_returns_ready(client: TestClient) -> None:
    resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"


def test_hello_includes_hostname(client: TestClient) -> None:
    resp = client.get("/hello")
    assert resp.status_code == 200
    body = resp.json()
    assert "message" in body
    assert "pod_hostname" in body
    assert body["pod_hostname"]  # non-empty
