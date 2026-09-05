"""Auth: token verification, and the data boundary between users."""

from io import BytesIO

import jwt
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app import auth
from app.config import settings

SECRET = "test-secret"


@pytest.fixture
def hs256(monkeypatch):
    """Point verification at a symmetric secret we control."""
    monkeypatch.setattr(settings, "supabase_jwt_secret", SECRET)
    monkeypatch.setattr(settings, "auth_enabled", True)


def _token(claims: dict, secret: str = SECRET) -> str:
    return jwt.encode({"aud": "authenticated", **claims}, secret, algorithm="HS256")


def test_valid_token_yields_subject(hs256):
    assert auth.verify_token(_token({"sub": "abc-123"})) == "abc-123"


def test_token_signed_with_wrong_secret_is_rejected(hs256):
    with pytest.raises(HTTPException) as exc:
        auth.verify_token(_token({"sub": "abc"}, secret="not-the-secret"))
    assert exc.value.status_code == 401


def test_expired_token_is_rejected(hs256):
    with pytest.raises(HTTPException) as exc:
        auth.verify_token(_token({"sub": "abc", "exp": 1000000000}))
    assert exc.value.status_code == 401


def test_wrong_audience_is_rejected(hs256):
    token = jwt.encode(
        {"sub": "abc", "aud": "some-other-service"}, SECRET, algorithm="HS256"
    )
    with pytest.raises(HTTPException) as exc:
        auth.verify_token(token)
    assert exc.value.status_code == 401


def test_token_without_subject_is_rejected(hs256):
    with pytest.raises(HTTPException) as exc:
        auth.verify_token(_token({}))
    assert exc.value.status_code == 401


def test_garbage_token_is_rejected(hs256):
    with pytest.raises(HTTPException) as exc:
        auth.verify_token("not.a.jwt")
    assert exc.value.status_code == 401


# --- The data boundary -----------------------------------------------------


def _upload(client: TestClient, csv: bytes) -> str:
    r = client.post("/upload", files={"file": ("t.csv", BytesIO(csv), "text/csv")})
    assert r.status_code == 202
    return r.json()["job_id"]


def test_user_cannot_read_another_users_job(client, as_user, sample_csv):
    job_id = _upload(client, sample_csv)
    assert client.get(f"/job/{job_id}").status_code == 200

    as_user("user-b")
    r = client.get(f"/job/{job_id}")
    # 404 rather than 403: a 403 would confirm the job exists.
    assert r.status_code == 404


def test_user_cannot_simulate_against_another_users_analysis(
    client, as_user, sample_csv
):
    job_id = _upload(client, sample_csv)
    as_user("user-b")
    r = client.post(
        "/simulate",
        json={
            "analysis_job_id": job_id,
            "goal_amount": 300.0,
            "months": 12,
            "cut_categories": ["Dining"],
        },
    )
    assert r.status_code == 404


def test_job_listing_is_scoped_to_the_caller(client, as_user, sample_csv):
    _upload(client, sample_csv)
    _upload(client, sample_csv)
    assert len(client.get("/jobs").json()) == 2

    as_user("user-b")
    assert client.get("/jobs").json() == []

    _upload(client, sample_csv)
    assert len(client.get("/jobs").json()) == 1

    as_user("user-a")
    assert len(client.get("/jobs").json()) == 2


def test_listing_is_newest_first(client, sample_csv):
    first = _upload(client, sample_csv)
    second = _upload(client, sample_csv)
    returned = [j["job_id"] for j in client.get("/jobs").json()]
    assert returned == [second, first]
