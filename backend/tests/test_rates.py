"""Exchange rate endpoint: caching, and behaviour when the upstream is down."""

import time

import httpx
import pytest

from app import rates


@pytest.fixture(autouse=True)
def clean_cache():
    rates._cache._local.clear()
    rates._cache._client = None  # force the in-process cache
    yield
    rates._cache._local.clear()


def _payload(eur=0.9):
    return {
        "amount": 1.0,
        "base": "USD",
        "date": "2026-09-04",
        "rates": {"EUR": eur, "GBP": 0.74},
    }


def test_fetches_and_includes_the_base_currency(monkeypatch):
    monkeypatch.setattr(rates.httpx, "get", lambda *a, **k: httpx.Response(
        200, json=_payload(), request=httpx.Request("GET", rates.API_URL)))
    result = rates.get_rates("USD")
    assert result["rates"]["EUR"] == 0.9
    # The base is included as 1.0 so the UI needn't special-case it.
    assert result["rates"]["USD"] == 1.0
    assert result["cached"] is False


def test_second_call_is_served_from_cache(monkeypatch):
    calls = {"n": 0}

    def fake_get(*a, **k):
        calls["n"] += 1
        return httpx.Response(200, json=_payload(),
                              request=httpx.Request("GET", rates.API_URL))

    monkeypatch.setattr(rates.httpx, "get", fake_get)
    rates.get_rates("USD")
    second = rates.get_rates("USD")
    assert calls["n"] == 1
    assert second["cached"] is True


def test_stale_entry_is_served_when_upstream_fails(monkeypatch):
    monkeypatch.setattr(rates.httpx, "get", lambda *a, **k: httpx.Response(
        200, json=_payload(), request=httpx.Request("GET", rates.API_URL)))
    rates.get_rates("USD")

    # Age the entry past its freshness window, then break the upstream.
    entry = rates._cache.get("rates:USD")
    entry["fetched_at"] = time.time() - (rates.FRESH_FOR_SECONDS + 1)
    rates._cache.set("rates:USD", entry)

    def boom(*a, **k):
        raise httpx.ConnectError("upstream down")

    monkeypatch.setattr(rates.httpx, "get", boom)
    result = rates.get_rates("USD")
    assert result["stale"] is True
    assert result["rates"]["EUR"] == 0.9


def test_failure_without_a_cached_entry_raises(monkeypatch):
    def boom(*a, **k):
        raise httpx.ConnectError("upstream down")

    monkeypatch.setattr(rates.httpx, "get", boom)
    with pytest.raises(httpx.HTTPError):
        rates.get_rates("USD")


def test_endpoint_returns_rates(client, monkeypatch):
    monkeypatch.setattr(rates.httpx, "get", lambda *a, **k: httpx.Response(
        200, json=_payload(), request=httpx.Request("GET", rates.API_URL)))
    r = client.get("/rates")
    assert r.status_code == 200
    assert r.json()["rates"]["EUR"] == 0.9


def test_endpoint_reports_503_when_rates_cannot_be_had(client, monkeypatch):
    def boom(*a, **k):
        raise httpx.ConnectError("upstream down")

    monkeypatch.setattr(rates.httpx, "get", boom)
    assert client.get("/rates").status_code == 503
