"""
SQLAlchemy ORM models — Veritas Claims Analytics (Real Schema)

Matches the company's 79-column output schema exactly.
One row per test result (lab_report) or per medication (discharge_summary).

Tables:
    - pipeline_runs         : Batch run metadata
    - standardized_records  : The main flat output table (matches BigQuery schema)
    - error_logs            : Processing errors per file
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey,
    Integer, String, Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.engine import Base


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# PipelineRun
# ---------------------------------------------------------------------------
class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_id: Mapped[str] = mapped_column(String(36), unique=True, default=_uuid)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="running")
    total_files: Mapped[int] = mapped_column(Integer, default=0)
    processed: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)
    total_records: Mapped[int] = mapped_column(Integer, default=0)
    flagged_records: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    error_logs: Mapped[list["ErrorLog"]] = relationship(back_populates="pipeline_run")
    records: Mapped[list["StandardizedRecord"]] = relationship(back_populates="pipeline_run")


# ---------------------------------------------------------------------------
# StandardizedRecord  — main output table (flat, one row per result/medication)
# ---------------------------------------------------------------------------
class StandardizedRecord(Base):
    """
    Flat output table matching the company's BigQuery schema.
    record_type = 'lab_result'        → test columns populated, medication columns NULL
    record_type = 'discharge_medication' → medication columns populated, test columns NULL
    record_type = 'discharge_summary' → discharge header only (no test, no med)
    """
    __tablename__ = "standardized_records"

    # --- Primary key ---
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)

    # --- Pipeline linkage ---
    run_id: Mapped[int] = mapped_column(Integer, ForeignKey("pipeline_runs.id"), index=True)
    record_type: Mapped[str] = mapped_column(String(50), index=True)
    filename: Mapped[str] = mapped_column(String(300))
    file_gcs_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # --- Document identifiers (from Veritas API wrapper) ---
    document_id: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    trace_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    correlation_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source_system: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    claim_no: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    nt_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    consumer_client_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    destination_identifier: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    metadetails: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string

    # --- Patient demographics ---
    patient_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    age: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    uhid: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    hospital_name: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    lab_or_hospital_name: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    doctor_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    bill_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reports_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # --- Lab test result (populated for record_type='lab_result') ---
    test_name_canonical: Mapped[Optional[str]] = mapped_column(String(300), index=True, nullable=True)
    test_name_original: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    result_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    result_text: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    unit_canonical: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    unit_original: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    range_low: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    range_high: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    range_text: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    test_analytics: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    normalization_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    normalization_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    page_no: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # --- Discharge summary fields ---
    admission_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    discharge_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    diagnosis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    brief_history: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    general_examinations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommendations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hospital_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ward: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    post_discharge_advice: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    course_during_hospitalisation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    medicine_injections_investigation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # --- Medication fields (populated for record_type='discharge_medication') ---
    medicine: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    dose: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    frequency: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    medicine_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # --- Audit ---
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    pipeline_run: Mapped["PipelineRun"] = relationship(back_populates="records")


# ---------------------------------------------------------------------------
# ErrorLog
# ---------------------------------------------------------------------------
class ErrorLog(Base):
    __tablename__ = "error_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_id: Mapped[int] = mapped_column(Integer, ForeignKey("pipeline_runs.id"))
    filename: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    error_type: Mapped[str] = mapped_column(String(100))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    pipeline_run: Mapped["PipelineRun"] = relationship(back_populates="error_logs")
