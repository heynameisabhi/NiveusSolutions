"""
Pydantic schemas for API request/response serialization.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Pipeline Run
# ---------------------------------------------------------------------------
class PipelineRunOut(BaseModel):
    id: int
    run_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    total_files: int
    processed: int
    failed: int
    flagged: int
    duration_seconds: Optional[float] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Clinic
# ---------------------------------------------------------------------------
class ClinicOut(BaseModel):
    id: int
    clinic_id: str
    clinic_name: str
    config_file: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ClinicAnalyticsOut(BaseModel):
    clinic_id: str
    clinic_name: str
    total_reports: int
    duplicate_count: int
    duplicate_rate: float
    flagged_count: int
    error_count: int
    error_rate: float


# ---------------------------------------------------------------------------
# Flagged Record
# ---------------------------------------------------------------------------
class FlaggedRecordOut(BaseModel):
    id: int
    standardized_report_id: int
    field_name: str
    raw_value: Optional[str] = None
    numeric_value: Optional[float] = None
    unit: Optional[str] = None
    classification: str
    reference_min: Optional[float] = None
    reference_max: Optional[float] = None
    flagged_at: datetime
    # Joined fields
    patient_name: Optional[str] = None
    clinic_id: Optional[str] = None
    report_date: Optional[str] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Standardized Report (list)
# ---------------------------------------------------------------------------
class StandardizedReportOut(BaseModel):
    id: int
    raw_report_id: int
    clinic_id: str
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    report_date: Optional[str] = None
    is_duplicate: bool
    processed_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Record Inspector (detail with raw + standardized side-by-side)
# ---------------------------------------------------------------------------
class RecordDetailOut(BaseModel):
    id: int
    clinic_id: str
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    report_date: Optional[str] = None
    is_duplicate: bool
    processed_at: datetime
    standardized_data: dict[str, Any]
    medications: Optional[list[str]] = None
    raw_json: dict[str, Any]          # original JSON
    flagged_records: list[FlaggedRecordOut] = []

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Dashboard summary
# ---------------------------------------------------------------------------
class DashboardStatsOut(BaseModel):
    total_files: int
    processed: int
    failed: int
    flagged: int
    duplicate_count: int
    last_run_at: Optional[datetime] = None
    last_run_duration: Optional[float] = None
    classification_breakdown: dict[str, int]
    runs: list[PipelineRunOut]


# ---------------------------------------------------------------------------
# Ingest request
# ---------------------------------------------------------------------------
class IngestRequest(BaseModel):
    folder: Optional[str] = None   # defaults to INGEST_FOLDER env var
    clinic_id: Optional[str] = None  # if None, auto-detect from JSON
