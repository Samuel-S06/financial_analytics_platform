"""Redis-backed job store with in-memory fallback."""

import io
import json
import logging
import uuid
from threading import Lock
from typing import Any

import pandas as pd
import redis

from app.config import settings

log = logging.getLogger(__name__)

PENDING = "pending"
RUNNING = "running"
DONE = "done"
FAILED = "failed"


class JobStore:
    def create(self) -> str:
        raise NotImplementedError

    def set_status(
        self, job_id: str, status: str, error: str | None = None
    ) -> None:
        raise NotImplementedError

    def set_result(self, job_id: str, result: dict[str, Any]) -> None:
        raise NotImplementedError

    def get(self, job_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    def set_dataframe(self, job_id: str, df: pd.DataFrame) -> None:
        raise NotImplementedError

    def get_dataframe(self, job_id: str) -> pd.DataFrame | None:
        raise NotImplementedError


class RedisJobStore(JobStore):
    def __init__(self, host: str, port: int, ttl: int):
        # decode_responses=False because DataFrames are stored as binary parquet.
        # JSON records get decoded manually.
        self.client = redis.Redis(host=host, port=port, decode_responses=False)
        self.ttl = ttl

    @staticmethod
    def _key(job_id: str) -> str:
        return f"job:{job_id}"

    @staticmethod
    def _df_key(job_id: str) -> str:
        return f"df:{job_id}"

    def create(self) -> str:
        job_id = str(uuid.uuid4())
        record = {"job_id": job_id, "status": PENDING, "error": None, "result": None}
        self.client.set(self._key(job_id), json.dumps(record).encode(), ex=self.ttl)
        return job_id

    def set_status(
        self, job_id: str, status: str, error: str | None = None
    ) -> None:
        record = self.get(job_id)
        if record is None:
            return
        record["status"] = status
        if error is not None:
            record["error"] = error
        self.client.set(self._key(job_id), json.dumps(record).encode(), ex=self.ttl)

    def set_result(self, job_id: str, result: dict[str, Any]) -> None:
        record = self.get(job_id)
        if record is None:
            return
        record["status"] = DONE
        record["result"] = result
        self.client.set(self._key(job_id), json.dumps(record).encode(), ex=self.ttl)

    def get(self, job_id: str) -> dict[str, Any] | None:
        raw = self.client.get(self._key(job_id))
        return json.loads(raw.decode()) if raw else None

    def set_dataframe(self, job_id: str, df: pd.DataFrame) -> None:
        # Parquet preserves dtypes and is faster than pickle for tabular data.
        buf = io.BytesIO()
        df.to_parquet(buf, engine="pyarrow")
        meta_key = f"{self._df_key(job_id)}:meta"
        self.client.set(self._df_key(job_id), buf.getvalue(), ex=self.ttl)
        self.client.set(meta_key, json.dumps(dict(df.attrs)).encode(), ex=self.ttl)

    def get_dataframe(self, job_id: str) -> pd.DataFrame | None:
        raw = self.client.get(self._df_key(job_id))
        if raw is None:
            return None
        df = pd.read_parquet(io.BytesIO(raw), engine="pyarrow")
        meta = self.client.get(f"{self._df_key(job_id)}:meta")
        if meta:
            df.attrs.update(json.loads(meta.decode()))
        return df

    def ping(self) -> bool:
        try:
            return self.client.ping()
        except redis.ConnectionError:
            return False


class InMemoryJobStore(JobStore):
    def __init__(self):
        self._jobs: dict[str, dict[str, Any]] = {}
        self._dfs: dict[str, pd.DataFrame] = {}
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

    def set_status(
        self, job_id: str, status: str, error: str | None = None
    ) -> None:
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

    def set_dataframe(self, job_id: str, df: pd.DataFrame) -> None:
        with self._lock:
            self._dfs[job_id] = df

    def get_dataframe(self, job_id: str) -> pd.DataFrame | None:
        with self._lock:
            return self._dfs.get(job_id)

    def ping(self) -> bool:
        return True


def _make_store() -> JobStore:
    if settings.use_redis:
        return RedisJobStore(
            host=settings.redis_host,
            port=settings.redis_port,
            ttl=settings.job_ttl_seconds,
        )
    return InMemoryJobStore()


store: JobStore = _make_store()
