"""
Background job runners.

These functions are submitted to FastAPI's BackgroundTasks queue. Each one
takes a job_id (so it can write status updates to the store) plus its inputs.

Why background tasks rather than running synchronously: pandas operations on
a large CSV could take several seconds. Holding the HTTP connection open
that long is bad UX (timeouts, retries) and bad for resource utilization
(each pending request occupies a worker). Submitting a job and polling for
completion is the standard pattern.
"""

import logging
import traceback

import pandas as pd

from app.analysis import analytics, parser, simulation
from app.analysis.parser import ParseError
from app.job_store import RUNNING, store

log = logging.getLogger(__name__)


# Where we stash the parsed DataFrame for each upload job, keyed by job_id.
# This is process-local: a simulation submitted to a different pod than the
# upload was processed on won't find the data here.
#
# Tradeoff: storing pandas DataFrames in Redis would mean serializing them on
# every read/write, which is slow and brittle. For this demo, we accept the
# constraint that simulations and uploads must hit the same pod's data and
# document it. In a real system you'd put the parsed data in object storage
# (S3) keyed by job_id and load on demand.
_dataframes: dict[str, pd.DataFrame] = {}


def run_upload_job(job_id: str, csv_bytes: bytes) -> None:
    """
    Background task: parse a CSV upload and run the full analysis.

    Updates the job store throughout: pending -> running -> done|failed.
    Also caches the parsed DataFrame so subsequent simulation jobs can use it.
    """
    log.info("upload job starting", extra={"job_id": job_id})
    store.set_status(job_id, RUNNING)
    try:
        df = parser.parse_csv(csv_bytes)
        result = analytics.full_analysis(df)
        # Cache the DataFrame for later simulation jobs against this upload.
        _dataframes[job_id] = df
        store.set_result(job_id, result)
        log.info("upload job done", extra={"job_id": job_id})
    except ParseError as exc:
        # Expected failure mode - bad input. Surface the exact message to the
        # user so they can fix their CSV.
        log.info("upload job failed (parse error)", extra={"job_id": job_id, "error": str(exc)})
        store.set_status(job_id, "failed", error=str(exc))
    except Exception as exc:  # noqa: BLE001 - we want to catch anything here
        # Unexpected failure - log a stack trace for debugging, but only show
        # a generic message to the user (don't leak internals).
        log.exception("upload job crashed", extra={"job_id": job_id})
        store.set_status(
            job_id, "failed",
            error=f"Internal error during analysis: {type(exc).__name__}",
        )
        # Also log the traceback in case it's useful when debugging
        log.debug(traceback.format_exc())


def run_simulation_job(
    job_id: str,
    analysis_job_id: str,
    goal_amount: float,
    months: int,
    cut_categories: list[str],
) -> None:
    """
    Background task: run a savings simulation against a previously-uploaded
    dataset. Requires the analysis job_id to be present in this pod's cache.
    """
    log.info("simulation job starting", extra={"job_id": job_id})
    store.set_status(job_id, RUNNING)
    try:
        df = _dataframes.get(analysis_job_id)
        if df is None:
            raise ValueError(
                f"No data found for analysis job {analysis_job_id}. "
                "It may have been processed by a different pod, or the upload "
                "job hasn't completed yet."
            )

        req = simulation.SimulationRequest(
            goal_amount=goal_amount,
            months=months,
            cut_categories=cut_categories,
        )
        result = simulation.simulate(df, req)
        store.set_result(job_id, result)
        log.info("simulation job done", extra={"job_id": job_id})
    except ValueError as exc:
        log.info("simulation job failed", extra={"job_id": job_id, "error": str(exc)})
        store.set_status(job_id, "failed", error=str(exc))
    except Exception as exc:  # noqa: BLE001
        log.exception("simulation job crashed", extra={"job_id": job_id})
        store.set_status(
            job_id, "failed",
            error=f"Internal error during simulation: {type(exc).__name__}",
        )