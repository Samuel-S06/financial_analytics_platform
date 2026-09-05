"""
Live exchange rates, fetched from Frankfurter and cached in Redis.

Frankfurter (https://frankfurter.dev) publishes ECB reference rates, needs no
API key, and updates once a working day - so a long cache costs nothing in
accuracy and keeps us off their servers.

The call is made here rather than from the browser on purpose: it reuses the
Redis the app already runs, so one fetch serves every user and every pod, and
it keeps the upstream dependency behind our own API surface.
"""

import json
import logging
import time
from typing import Any

import httpx
import redis

from app.config import settings

log = logging.getLogger(__name__)

API_URL = "https://api.frankfurter.dev/v1/latest"
REQUEST_TIMEOUT_SECONDS = 5.0

# Rates are considered current for an hour. Entries are kept far longer so a
# stale one can still be served if the upstream API is unreachable - a day-old
# rate beats an error page for what is a display convenience.
FRESH_FOR_SECONDS = 60 * 60
KEEP_FOR_SECONDS = 60 * 60 * 24 * 7

# A deliberately short list: enough to demonstrate the toggle without turning
# the picker into a scrolling wall. All are ECB-published.
SUPPORTED = ("EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "INR", "MXN", "BRL")


class _Cache:
    """Redis when available, an in-process dict otherwise (tests, USE_REDIS=false)."""

    def __init__(self) -> None:
        self._client: redis.Redis | None = None
        self._local: dict[str, str] = {}
        if settings.use_redis:
            self._client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                decode_responses=True,
            )

    def get(self, key: str) -> dict[str, Any] | None:
        try:
            raw = self._client.get(key) if self._client else self._local.get(key)
        except redis.RedisError:
            # A cache outage must not take the endpoint down with it.
            log.warning("rate cache unreachable; falling back to a live fetch")
            return None
        return json.loads(raw) if raw else None

    def set(self, key: str, value: dict[str, Any]) -> None:
        payload = json.dumps(value)
        try:
            if self._client:
                self._client.set(key, payload, ex=KEEP_FOR_SECONDS)
            else:
                self._local[key] = payload
        except redis.RedisError:
            log.warning("could not write rate cache")


_cache = _Cache()


def _fetch(base: str) -> dict[str, Any]:
    response = httpx.get(
        API_URL,
        params={"base": base, "symbols": ",".join(SUPPORTED)},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    body = response.json()
    return {
        "base": body["base"],
        "date": body["date"],
        # The base itself is always 1, and including it lets the UI treat the
        # display currency uniformly instead of special-casing USD.
        "rates": {body["base"]: 1.0, **body["rates"]},
        "fetched_at": time.time(),
    }


def get_rates(base: str = "USD") -> dict[str, Any]:
    """
    Current rates for `base`, cached.

    Raises httpx.HTTPError only when there is no usable cached entry to fall
    back on.
    """
    key = f"rates:{base}"
    cached = _cache.get(key)
    age = time.time() - cached["fetched_at"] if cached else None

    if cached and age < FRESH_FOR_SECONDS:
        return {**cached, "cached": True, "stale": False}

    try:
        fresh = _fetch(base)
    except httpx.HTTPError as exc:
        if cached:
            log.warning(
                "rate fetch failed; serving a stale entry",
                extra={"error": type(exc).__name__, "age_seconds": int(age)},
            )
            return {**cached, "cached": True, "stale": True}
        raise

    _cache.set(key, fresh)
    return {**fresh, "cached": False, "stale": False}
