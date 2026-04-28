"""
Job store - tracks the state and results of async jobs.

Why this exists: with multiple backend replicas behind a Service, a job
submitted to pod A might be polled from pod B. An in-process dict won't work.
Redis is the simplest shared-state solution.

We also support an in-memory fallback (use_redis=False) for tests, so the
test suite doesn't need a running Redis instance.

Job lifecycle:
    pending -> running -> done    (success path)
                       -> failed  (with an error message)
"""

import json
import logging
import uuid
from threading import Lock
from typing import Any

import redis

from app.config import settings

log = logging.getLogger(__name__)


# Job state constants. Strings rather than an Enum because they cross JSON
# boundaries to the frontend and string values are easier to debug.
PENDING = "pending"
RUNNING = "running"
DONE = "done"
FAILED = "failed"


class JobStore:
    """Abstract interface implemented by both Redis and in-memory backends."""

    def create(self) -> str:
        """Create a new job in PENDING state and return its id."""
        raise NotImplementedError

    def set_status(self, job_id: str, status: str, error: str | None = None) -> None:
        raise NotImplementedError

    def set_result(self, job_id: str, result: dict[str, Any]) -> None:
        """Store the final result and mark as DONE."""
        raise NotImplementedError

    def get(self, job_id: str) -> dict[str, Any] | None:
        """Return the full job record, or None if not found."""
        raise NotImplementedError


# --- Redis backend ----------------------------------------------------------

class RedisJobStore(JobStore):
    """Persists job state in Redis under keys like 'job:<uuid>'."""

    def __init__(self, host: str, port: int, ttl: int):
        # decode_responses=True means we get strings back instead of bytes,
        # which is what we want for JSON.
        self.client = redis.Redis(host=host, port=port, decode_responses=True)
        self.ttl = ttl

    @staticmethod
    def _key(job_id: str) -> str:
        return f"job:{job_id}"

    def create(self) -> str:
        job_id = str(uuid.uuid4())
        record = {"job_id": job_id, "status": PENDING, "error": None, "result": None}
        # SET with EX: store the JSON blob with an expiration. After the TTL
        # the key is automatically deleted - prevents Redis from growing
        # unboundedly with stale jobs.
        self.client.set(self._key(job_id), json.dumps(record), ex=self.ttl)
        log.info("job created", extra={"job_id": job_id})
        return job_id

    def set_status(self, job_id: str, status: str, error: str | None = None) -> None:
        record = self.get(job_id)
        if record is None:
            log.warning("set_status on unknown job", extra={"job_id": job_id})
            return
        record["status"] = status
        if error is not None:
            record["error"] = error
        self.client.set(self._key(job_id), json.dumps(record), ex=self.ttl)
        log.info("job status updated", extra={"job_id": job_id, "status": status})

    def set_result(self, job_id: str, result: dict[str, Any]) -> None:
        record = self.get(job_id)
        if record is None:
            log.warning("set_result on unknown job", extra={"job_id": job_id})
            return
        record["status"] = DONE
        record["result"] = result
        self.client.set(self._key(job_id), json.dumps(record), ex=self.ttl)
        log.info("job completed", extra={"job_id": job_id})

    def get(self, job_id: str) -> dict[str, Any] | None:
        raw = self.client.get(self._key(job_id))
        if raw is None:
            return None
        return json.loads(raw)

    def ping(self) -> bool:
        """Health check - returns True if Redis is reachable."""
        try:
            return self.client.ping()
        except redis.ConnectionError:
            return False


# --- In-memory backend (tests, fallback) ------------------------------------

class InMemoryJobStore(JobStore):
    """A dict-backed store for tests and single-replica development."""

    def __init__(self):
        self._jobs: dict[str, dict[str, Any]] = {}
        # Lock because BackgroundTasks may write while a request reads.
        self._lock = Lock()

    def create(self) -> str:
        job_id = str(uuid.uuid4())
        with self._lock:
            self._jobs[job_id] = {
                "job_id": job_id,
                "status": PENDING,
                "error": None,
                "result": None,
            }
        return job_id

    def set_status(self, job_id: str, status: str, error: str | None = None) -> None:
        with self._lock:
            if job_id not in self._jobs:
                return
            self._jobs[job_id]["status"] = status
            if error is not None:
                self._jobs[job_id]["error"] = error

    def set_result(self, job_id: str, result: dict[str, Any]) -> None:
        with self._lock:
            if job_id not in self._jobs:
                return
            self._jobs[job_id]["status"] = DONE
            self._jobs[job_id]["result"] = result

    def get(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._jobs.get(job_id)

    def ping(self) -> bool:
        return True


# --- Factory ----------------------------------------------------------------

# Single shared instance per pod. Created at import time based on config.
# Tests can replace this via a fixture (see conftest.py).
def _make_store() -> JobStore:
    if settings.use_redis:
        return RedisJobStore(
            host=settings.redis_host,
            port=settings.redis_port,
            ttl=settings.job_ttl_seconds,
        )
    return InMemoryJobStore()


store: JobStore = _make_store()