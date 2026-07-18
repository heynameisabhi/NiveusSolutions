"""
Loader Module — Insert standardized records into the database.

Handles:
- Idempotent insert by document_id + test_name_original + record_type
  (prevents duplicate rows from re-running the same file)
- Bulk inserts for performance
- Final stats update on PipelineRun
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.models import ErrorLog, PipelineRun, StandardizedRecord

logger = logging.getLogger(__name__)

# Fields that drive uniqueness for dedup
_LAB_DEDUP_FIELDS = ("document_id", "test_name_original", "page_no")
_MED_DEDUP_FIELDS = ("document_id", "medicine", "dose", "frequency")


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _build_dedup_key(rec: dict) -> str:
    if rec.get("record_type") in ("lab_result",):
        parts = [str(rec.get(f) or "") for f in _LAB_DEDUP_FIELDS]
    else:
        parts = [str(rec.get(f) or "") for f in _MED_DEDUP_FIELDS]
    return "|".join(parts)


def load_records(
    session: Session,
    records: list[dict],
    run: PipelineRun,
) -> dict:
    """
    Insert records into the DB.

    Args:
        session: SQLAlchemy session
        records:  flat record dicts from the standardizer
        run:      PipelineRun ORM instance to update

    Returns:
        stats dict with inserted / skipped counts
    """
    if not records:
        return {"inserted": 0, "skipped": 0}

    # Build existing dedup keys for this document to prevent double-inserts
    document_ids = {r.get("document_id") for r in records if r.get("document_id")}
    existing_keys: set[str] = set()

    for doc_id in document_ids:
        existing = session.execute(
            select(
                StandardizedRecord.document_id,
                StandardizedRecord.test_name_original,
                StandardizedRecord.page_no,
                StandardizedRecord.medicine,
                StandardizedRecord.dose,
                StandardizedRecord.frequency,
                StandardizedRecord.record_type,
            ).where(StandardizedRecord.document_id == doc_id)
        ).all()
        for row in existing:
            rec_dict = dict(row._mapping)
            existing_keys.add(_build_dedup_key(rec_dict))

    inserted = 0
    skipped = 0
    now = _now()

    for rec_dict in records:
        dedup_key = _build_dedup_key(rec_dict)
        if dedup_key in existing_keys:
            skipped += 1
            continue

        obj = StandardizedRecord(
            id=str(uuid.uuid4()),
            run_id=run.id,
            processed_at=now,
            ingested_at=now,
            **{
                k: v for k, v in rec_dict.items()
                if hasattr(StandardizedRecord, k) and k != "id"
            },
        )
        session.add(obj)
        existing_keys.add(dedup_key)
        inserted += 1

    session.flush()

    logger.info(
        "Loaded run_id=%s: %d inserted, %d skipped (dedup)",
        run.run_id, inserted, skipped,
    )
    return {"inserted": inserted, "skipped": skipped}


def log_error(
    session: Session,
    run: PipelineRun,
    filename: str,
    error_type: str,
    message: str,
) -> None:
    """Record a processing error linked to the current pipeline run."""
    entry = ErrorLog(
        run_id=run.id,
        filename=filename,
        error_type=error_type,
        message=str(message)[:4000],
        created_at=_now(),
    )
    session.add(entry)
