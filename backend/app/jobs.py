"""Background job runners."""

import logging

from app import job_store
from app.analysis import analytics, parser, simulation
from app.analysis.parser import ParseError
from app.job_store import RUNNING

log = logging.getLogger(__name__)


def run_upload_job(job_id: str, csv_bytes: bytes) -> None:
    log.info("upload job starting", extra={"job_id": job_id})
    job_store.store.set_status(job_id, RUNNING)
    try:
        df = parser.parse_csv(csv_bytes)
        result = analytics.full_analysis(df)
        # Persist the parsed DataFrame to the store so simulation jobs can find
        # it regardless of which pod they land on.
        job_store.store.set_dataframe(job_id, df)
        job_store.store.set_result(job_id, result)
    except ParseError as exc:
        job_store.store.set_status(job_id, "failed", error=str(exc))
    except Exception as exc:
        log.exception("upload job crashed", extra={"job_id": job_id})
        job_store.store.set_status(job_id, "failed", error=f"Internal error: {type(exc).__name__}")


def run_simulation_job(job_id: str, analysis_job_id: str, goal_amount: float,
                       months: int, cut_categories: list[str]) -> None:
    log.info("simulation job starting", extra={"job_id": job_id})
    job_store.store.set_status(job_id, RUNNING)
    try:
        df = job_store.store.get_dataframe(analysis_job_id)
        if df is None:
            raise ValueError(
                f"No data found for analysis job {analysis_job_id}. "
                "The upload may have expired or failed."
            )

        req = simulation.SimulationRequest(
            goal_amount=goal_amount, months=months, cut_categories=cut_categories,
        )
        result = simulation.simulate(df, req)
        job_store.store.set_result(job_id, result)
    except ValueError as exc:
        job_store.store.set_status(job_id, "failed", error=str(exc))
    except Exception as exc:
        log.exception("simulation job crashed", extra={"job_id": job_id})
        job_store.store.set_status(job_id, "failed", error=f"Internal error: {type(exc).__name__}")
