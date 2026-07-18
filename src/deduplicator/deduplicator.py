"""
Deduplication Module

Detects duplicate reports using a configurable strategy.

Strategy: compute a hash of configurable key fields
(patient_id + clinic_id + report_date) and check DB for existing entry.
"""
from __future__ import annotations

import hashlib
import logging
from typing import Any

from sqlalchemy.orm import Session

from src.models.models import StandardizedReport

logger = logging.getLogger(__name__)


def _make_dedup_key(standardized: dict, dedup_fields: list[str]) -> str:
    """
    Build a dedup key string from specified fields.
    Handles nested access with dot-notation.
    """
    parts = []
    for f in dedup_fields:
        if f == "clinic_id":
            parts.append(str(standardized.get("clinic_id", "")))
        elif f == "patient_id":
            parts.append(str(standardized.get("patient_id", "")))
        elif f == "report_date":
            parts.append(str(standardized.get("report_date", "")))
        else:
            parts.append(str(standardized.get(f, "")))
    return "|".join(parts)


def compute_dedup_hash(standardized: dict, dedup_fields: list[str]) -> str:
    """
    Compute MD5 of the dedup key.
    This is used to quickly check for duplicates in the DB.
    """
    key = _make_dedup_key(standardized, dedup_fields)
    return hashlib.md5(key.encode()).hexdigest()


def is_duplicate(
    standardized: dict,
    dedup_fields: list[str],
    raw_report_hash: str,
    db: Session,
) -> bool:
    """
    Check if this report is a duplicate.

    Two checks:
    1. Exact content hash match (raw JSON identical)
    2. Dedup key match (same patient + clinic + date)

    Returns True if duplicate.
    """
    # Check 1: exact content hash
    from src.models.models import RawReport
    existing_raw = (
        db.query(RawReport)
        .filter(RawReport.report_hash == raw_report_hash)
        .first()
    )
    if existing_raw:
        logger.info("Duplicate detected by content hash: %s", raw_report_hash)
        return True

    # Check 2: dedup key match
    patient_id = standardized.get("patient_id")
    clinic_id = standardized.get("clinic_id")
    report_date = standardized.get("report_date")

    if patient_id and clinic_id and report_date and "report_date" in dedup_fields:
        existing = (
            db.query(StandardizedReport)
            .filter(
                StandardizedReport.patient_id == str(patient_id),
                StandardizedReport.clinic_id == str(clinic_id),
                StandardizedReport.report_date == str(report_date),
            )
            .first()
        )
        if existing:
            logger.info(
                "Duplicate detected by key: patient=%s clinic=%s date=%s",
                patient_id, clinic_id, report_date,
            )
            return True

    return False
