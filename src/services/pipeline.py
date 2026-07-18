"""
Pipeline Orchestration — Veritas Claims

Runs the full pipeline:
  Ingest → Parse → Standardize → Load

Stats are tracked per-run in the PipelineRun table.
"""
from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from src.config_loader.loader import get_test_mapping
from src.ingestion.ingestion import scan_folder
from src.loader.loader import load_records, log_error
from src.models.models import PipelineRun
from src.parser.parser import parse_document
from src.standardizer.standardizer import ClinicalStandardizer, standardize_records

logger = logging.getLogger(__name__)

DEFAULT_SAMPLE_FOLDER = str(Path(__file__).parent.parent.parent / "sample-data")


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def run_pipeline(session: Session, folder: str = DEFAULT_SAMPLE_FOLDER) -> dict:
    """
    Execute the full pipeline on all JSON files in *folder*.

    Returns a result dict with run stats.
    """
    run = PipelineRun(
        run_id=str(uuid.uuid4()),
        started_at=_now(),
        status="running",
    )
    session.add(run)
    session.flush()  # get run.id

    t0 = time.perf_counter()
    total_inserted = 0
    total_skipped = 0

    # --- Load configs ---
    test_mapping = get_test_mapping()
    standardizer = ClinicalStandardizer(test_mapping)

    # --- Phase 1: Ingest ---
    ingest_result = scan_folder(folder)

    run.total_files = ingest_result.total
    run.failed = len(ingest_result.failed)

    # Log ingestion failures
    for fail in ingest_result.failed:
        log_error(
            session, run,
            filename=fail.get("filename", ""),
            error_type="ingestion_error",
            message=fail.get("error", "Unknown error"),
        )

    # --- Phase 2–4: Parse → Standardize → Load (per document) ---
    processed = 0
    for doc in ingest_result.documents:
        try:
            # Parse
            records = parse_document(doc)

            # Standardize (lab test name normalization)
            records = standardize_records(records, standardizer)

            # Load
            stats = load_records(session, records, run)
            total_inserted += stats["inserted"]
            total_skipped += stats["skipped"]

            processed += 1

        except Exception as exc:  # noqa: BLE001
            logger.exception("Pipeline error on %s: %s", doc.filename, exc)
            log_error(
                session, run,
                filename=doc.filename,
                error_type="pipeline_error",
                message=str(exc),
            )
            run.failed += 1

    # --- Finalize run ---
    duration = time.perf_counter() - t0
    run.processed = processed
    run.total_records = total_inserted
    run.status = "completed"
    run.completed_at = _now()
    run.duration_seconds = round(duration, 4)

    session.commit()

    result = {
        "status": "completed",
        "run_id": run.run_id,
        "total_files": run.total_files,
        "processed": run.processed,
        "failed": run.failed,
        "total_records_inserted": total_inserted,
        "total_records_skipped": total_skipped,
        "duration_seconds": run.duration_seconds,
    }
    logger.info("Pipeline complete: %s", result)
    return result
