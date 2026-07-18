"""
FastAPI Routes — Veritas Claims Analytics

Endpoints:
    GET  /api/dashboard              → overall stats + run history
    GET  /api/records                → paginated standardized records
    GET  /api/records/{id}           → single record detail
    GET  /api/lab-results            → lab results with optional filters
    GET  /api/medications            → discharge medications
    GET  /api/runs                   → pipeline run history
    POST /api/ingest                 → trigger pipeline run
    POST /api/upload/sample-data     → upload a sample JSON file
    POST /api/upload/clinic-config   → upload a clinic YAML config
    GET  /api/clinics/configs        → list all registered clinic configs
    DELETE /api/clinics/configs/{id} → delete a clinic config
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

import yaml
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from src.database.engine import get_db
from src.models.models import ErrorLog, PipelineRun, StandardizedRecord
from src.services.pipeline import DEFAULT_SAMPLE_FOLDER, run_pipeline

logger = logging.getLogger(__name__)
router = APIRouter()

# Resolve project-root-relative paths
_PROJECT_ROOT = Path(__file__).parent.parent.parent
SAMPLE_DATA_DIR = _PROJECT_ROOT / "sample-data"
CLINICS_CONFIG_DIR = _PROJECT_ROOT / "config" / "clinics"


# ---------------------------------------------------------------------------
# POST /api/upload/sample-data
# ---------------------------------------------------------------------------
@router.post("/upload/sample-data")
async def upload_sample_data(file: UploadFile = File(...)):
    """
    Upload a sample JSON data file to the sample-data folder.
    After upload, the file is available for the next pipeline run.
    """
    if not file.filename or not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Only .json files are accepted.")

    SAMPLE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    dest = SAMPLE_DATA_DIR / file.filename
    try:
        content = await file.read()
        dest.write_bytes(content)
        logger.info("Uploaded sample data file: %s", dest)
        return {"message": f"File '{file.filename}' uploaded successfully.", "path": str(dest)}
    except Exception as exc:
        logger.exception("Failed to save uploaded file: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# POST /api/upload/clinic-config
# ---------------------------------------------------------------------------
@router.post("/upload/clinic-config")
async def upload_clinic_config(file: UploadFile = File(...)):
    """
    Upload a clinic YAML config file to config/clinics/.
    The new clinic is immediately usable by the pipeline.
    """
    if not file.filename or not (file.filename.endswith(".yaml") or file.filename.endswith(".yml")):
        raise HTTPException(status_code=400, detail="Only .yaml / .yml files are accepted.")

    CLINICS_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    dest = CLINICS_CONFIG_DIR / file.filename
    try:
        content = await file.read()
        # Validate it is parseable YAML
        parsed = yaml.safe_load(content)
        if not isinstance(parsed, dict) or "clinic_id" not in parsed:
            raise ValueError("YAML must be a mapping containing at least 'clinic_id'.")
        dest.write_bytes(content)
        logger.info("Uploaded clinic config: %s", dest)
        return {
            "message": f"Clinic config '{file.filename}' uploaded successfully.",
            "clinic_id": parsed.get("clinic_id"),
            "clinic_name": parsed.get("clinic_name", ""),
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Failed to save clinic config: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# GET /api/clinics/configs  — list all registered clinic YAML configs
# ---------------------------------------------------------------------------
@router.get("/clinics/configs")
def list_clinic_configs():
    """Return metadata for all clinic YAML configs in config/clinics/."""
    configs = []
    if CLINICS_CONFIG_DIR.exists():
        for path in sorted(CLINICS_CONFIG_DIR.glob("*.yaml")):
            try:
                parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
                configs.append({
                    "filename": path.name,
                    "clinic_id": parsed.get("clinic_id", ""),
                    "clinic_name": parsed.get("clinic_name", ""),
                    "field_count": len(parsed.get("field_mappings", {})),
                })
            except Exception:
                configs.append({"filename": path.name, "clinic_id": "", "clinic_name": "(parse error)", "field_count": 0})
    return configs


# ---------------------------------------------------------------------------
# DELETE /api/clinics/configs/{clinic_id}
# ---------------------------------------------------------------------------
@router.delete("/clinics/configs/{clinic_id}")
def delete_clinic_config(clinic_id: str):
    """Delete a clinic YAML config by clinic_id."""
    if CLINICS_CONFIG_DIR.exists():
        for path in CLINICS_CONFIG_DIR.glob("*.yaml"):
            try:
                parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
                if parsed.get("clinic_id") == clinic_id:
                    path.unlink()
                    return {"message": f"Clinic '{clinic_id}' config deleted."}
            except Exception:
                continue
    raise HTTPException(status_code=404, detail=f"No config found for clinic_id='{clinic_id}'.")


# ---------------------------------------------------------------------------
# POST /api/ingest
# ---------------------------------------------------------------------------
@router.post("/ingest")
def ingest(folder: str = DEFAULT_SAMPLE_FOLDER, session: Session = Depends(get_db)):
    """Trigger a full pipeline run on the sample-data folder."""
    try:
        result = run_pipeline(session, folder=folder)
        return result
    except Exception as exc:
        logger.exception("Pipeline failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# GET /api/dashboard
# ---------------------------------------------------------------------------
@router.get("/dashboard")
def dashboard(session: Session = Depends(get_db)):
    """Aggregated stats for the dashboard."""
    total_files = session.execute(select(func.sum(PipelineRun.total_files))).scalar() or 0
    processed = session.execute(select(func.sum(PipelineRun.processed))).scalar() or 0
    failed = session.execute(select(func.sum(PipelineRun.failed))).scalar() or 0

    flagged = session.execute(
        select(func.count(StandardizedRecord.id)).where(
            StandardizedRecord.record_type == "lab_result",
            StandardizedRecord.test_analytics.in_(
                ["Above Range", "Below Range", "Outlier", "Invalid"]
            )
        )
    ).scalar_one()

    # Classification breakdown for the pie chart
    class_rows = session.execute(
        select(StandardizedRecord.test_analytics, func.count(StandardizedRecord.id))
        .where(
            StandardizedRecord.record_type == "lab_result",
            StandardizedRecord.test_analytics.in_(
                ["Above Range", "Below Range", "Outlier", "Invalid"]
            )
        )
        .group_by(StandardizedRecord.test_analytics)
    ).all()
    classification_breakdown = {row[0]: row[1] for row in class_rows}

    # Normalization method breakdown
    norm_rows = session.execute(
        select(StandardizedRecord.normalization_method, func.count(StandardizedRecord.id))
        .where(StandardizedRecord.record_type == "lab_result")
        .group_by(StandardizedRecord.normalization_method)
    ).all()
    normalization_breakdown = {row[0] or "unset": row[1] for row in norm_rows}

    # Canonical name distribution (top 10)
    top_tests = session.execute(
        select(StandardizedRecord.test_name_canonical, func.count(StandardizedRecord.id))
        .where(
            StandardizedRecord.record_type == "lab_result",
            StandardizedRecord.test_name_canonical != None,  # noqa: E711
        )
        .group_by(StandardizedRecord.test_name_canonical)
        .order_by(desc(func.count(StandardizedRecord.id)))
        .limit(10)
    ).all()
    top_tests_data = [{"name": r[0], "count": r[1]} for r in top_tests]

    # Source systems
    source_rows = session.execute(
        select(StandardizedRecord.source_system, func.count(StandardizedRecord.id))
        .group_by(StandardizedRecord.source_system)
    ).all()
    source_breakdown = {row[0] or "unknown": row[1] for row in source_rows}

    # Unique documents / claims
    unique_docs = session.execute(
        select(func.count(func.distinct(StandardizedRecord.document_id)))
    ).scalar_one()
    unique_claims = session.execute(
        select(func.count(func.distinct(StandardizedRecord.claim_no)))
    ).scalar_one()

    # Recent runs
    runs = session.execute(
        select(PipelineRun).order_by(desc(PipelineRun.started_at)).limit(10)
    ).scalars().all()

    last_run = runs[0] if runs else None

    return {
        "total_files": int(total_files),
        "processed": int(processed),
        "failed": int(failed),
        "flagged": flagged,
        "duplicate_count": 0,  # skipped during insertion
        "unique_documents": unique_docs,
        "unique_claims": unique_claims,
        "normalization_breakdown": normalization_breakdown,
        "source_breakdown": source_breakdown,
        "top_tests": top_tests_data,
        "classification_breakdown": classification_breakdown,
        "last_run_at": last_run.started_at.isoformat() if last_run else None,
        "last_run_duration": last_run.duration_seconds if last_run else None,
        "runs": [
            {
                "id": r.id,
                "run_id": r.run_id,
                "started_at": r.started_at.isoformat(),
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "status": r.status,
                "total_files": r.total_files,
                "processed": r.processed,
                "failed": r.failed,
                "total_records": r.total_records,
                "duration_seconds": r.duration_seconds,
            }
            for r in runs
        ],
    }


# ---------------------------------------------------------------------------
# GET /api/lab-results
# ---------------------------------------------------------------------------
@router.get("/lab-results")
def get_lab_results(
    claim_no: Optional[str] = None,
    document_id: Optional[str] = None,
    test_canonical: Optional[str] = None,
    normalization_method: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    session: Session = Depends(get_db),
):
    """Paginated lab test results with optional filters."""
    q = select(StandardizedRecord).where(StandardizedRecord.record_type == "lab_result")

    if claim_no:
        q = q.where(StandardizedRecord.claim_no == claim_no)
    if document_id:
        q = q.where(StandardizedRecord.document_id == document_id)
    if test_canonical:
        q = q.where(StandardizedRecord.test_name_canonical == test_canonical)
    if normalization_method:
        q = q.where(StandardizedRecord.normalization_method == normalization_method)

    total = session.execute(select(func.count()).select_from(q.subquery())).scalar_one()
    rows = session.execute(q.order_by(desc(StandardizedRecord.ingested_at)).offset(skip).limit(limit)).scalars().all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [_serialize_record(r) for r in rows],
    }


# ---------------------------------------------------------------------------
# GET /api/medications
# ---------------------------------------------------------------------------
@router.get("/medications")
def get_medications(
    claim_no: Optional[str] = None,
    document_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    session: Session = Depends(get_db),
):
    """Paginated discharge medications."""
    q = select(StandardizedRecord).where(
        StandardizedRecord.record_type.in_(["discharge_medication", "discharge_summary"])
    )
    if claim_no:
        q = q.where(StandardizedRecord.claim_no == claim_no)
    if document_id:
        q = q.where(StandardizedRecord.document_id == document_id)

    total = session.execute(select(func.count()).select_from(q.subquery())).scalar_one()
    rows = session.execute(q.order_by(desc(StandardizedRecord.ingested_at)).offset(skip).limit(limit)).scalars().all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [_serialize_record(r) for r in rows],
    }


# ---------------------------------------------------------------------------
# GET /api/flags
# ---------------------------------------------------------------------------
@router.get("/flags")
def get_flags(
    classification: Optional[str] = None,
    session: Session = Depends(get_db),
):
    """Get flagged/abnormal lab results."""
    q = select(StandardizedRecord).where(
        StandardizedRecord.record_type == "lab_result"
    )
    if classification and classification != "All":
        q = q.where(StandardizedRecord.test_analytics == classification)
    else:
        q = q.where(
            StandardizedRecord.test_analytics.in_(
                ["Above Range", "Below Range", "Outlier", "Invalid"]
            )
        )

    rows = session.execute(q.order_by(desc(StandardizedRecord.ingested_at))).scalars().all()
    return [_serialize_record(r) for r in rows]



# ---------------------------------------------------------------------------
# GET /api/records
# ---------------------------------------------------------------------------
@router.get("/records")
def get_records(
    record_type: Optional[str] = None,
    claim_no: Optional[str] = None,
    document_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    session: Session = Depends(get_db),
):
    """Paginated all records (lab_result + discharge_medication)."""
    q = select(StandardizedRecord)
    if record_type:
        q = q.where(StandardizedRecord.record_type == record_type)
    if claim_no:
        q = q.where(StandardizedRecord.claim_no == claim_no)
    if document_id:
        q = q.where(StandardizedRecord.document_id == document_id)

    total = session.execute(select(func.count()).select_from(q.subquery())).scalar_one()
    rows = session.execute(q.order_by(desc(StandardizedRecord.ingested_at)).offset(skip).limit(limit)).scalars().all()

    return {
        "total": total,
        "data": [_serialize_record(r) for r in rows],
    }


# ---------------------------------------------------------------------------
# GET /api/records/{id}
# ---------------------------------------------------------------------------
@router.get("/records/{record_id}")
def get_record(record_id: str, session: Session = Depends(get_db)):
    """Full detail for a single record."""
    rec = session.get(StandardizedRecord, record_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Record not found")
    return _serialize_record(rec)


# ---------------------------------------------------------------------------
# GET /api/runs
# ---------------------------------------------------------------------------
@router.get("/runs")
def get_runs(
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_db),
):
    """Pipeline run history."""
    runs = session.execute(
        select(PipelineRun).order_by(desc(PipelineRun.started_at)).limit(limit)
    ).scalars().all()
    return [
        {
            "id": r.id,
            "run_id": r.run_id,
            "started_at": r.started_at.isoformat(),
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            "status": r.status,
            "total_files": r.total_files,
            "processed": r.processed,
            "failed": r.failed,
            "total_records": r.total_records,
            "duration_seconds": r.duration_seconds,
        }
        for r in runs
    ]


# ---------------------------------------------------------------------------
# GET /api/claims  — unique claims summary
# ---------------------------------------------------------------------------
@router.get("/claims")
def get_claims(session: Session = Depends(get_db)):
    """Unique claims with record counts and patient metadata."""
    rows = session.execute(
        select(
            StandardizedRecord.claim_no,
            StandardizedRecord.document_id,
            StandardizedRecord.source_system,
            func.max(StandardizedRecord.patient_name).label("patient_name"),
            func.max(StandardizedRecord.reports_date).label("reports_date"),
            func.max(StandardizedRecord.admission_date).label("admission_date"),
            func.max(StandardizedRecord.hospital_name).label("hospital_name"),
            func.max(StandardizedRecord.age).label("age"),
            func.max(StandardizedRecord.gender).label("gender"),
            func.count(StandardizedRecord.id).label("record_count"),
            func.count(
                StandardizedRecord.id
            ).filter(StandardizedRecord.record_type == "lab_result").label("lab_count"),
        )
        .group_by(
            StandardizedRecord.claim_no,
            StandardizedRecord.document_id,
            StandardizedRecord.source_system,
        )
        .order_by(desc(func.count(StandardizedRecord.id)))
    ).all()

    return [
        {
            "claim_no": r.claim_no,
            "document_id": r.document_id,
            "source_system": r.source_system,
            "patient_name": r.patient_name,
            "reports_date": r.reports_date or r.admission_date or "—",
            "hospital_name": r.hospital_name or "—",
            "age": r.age,
            "gender": r.gender,
            "record_count": r.record_count,
            "lab_count": r.lab_count,
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# GET /api/documents/{document_id}
# ---------------------------------------------------------------------------
@router.get("/documents/{document_id}")
def get_document_details(document_id: str, session: Session = Depends(get_db)):
    """Retrieve full structured document details (demographics, lab results, medications)."""
    records = session.execute(
        select(StandardizedRecord)
        .where(StandardizedRecord.document_id == document_id)
        .order_by(desc(StandardizedRecord.ingested_at))
    ).scalars().all()

    if not records:
        raise HTTPException(status_code=404, detail="Document not found")

    # Group records
    lab_results = []
    medications = []

    # Common details from the first record
    first = records[0]

    for r in records:
        serialized = _serialize_record(r)
        if r.record_type == "lab_result":
            lab_results.append(serialized)
        elif r.record_type == "discharge_medication":
            medications.append(serialized)

    return {
        "document_id": document_id,
        "claim_no": first.claim_no,
        "trace_id": first.trace_id,
        "correlation_id": first.correlation_id,
        "source_system": first.source_system,
        "patient_name": first.patient_name,
        "age": first.age,
        "gender": first.gender,
        "uhid": first.uhid,
        "hospital_name": first.hospital_name or first.lab_or_hospital_name,
        "doctor_name": first.doctor_name,
        "reports_date": first.reports_date or first.admission_date,
        "admission_date": first.admission_date,
        "discharge_date": first.discharge_date,
        "diagnosis": first.diagnosis,
        "brief_history": first.brief_history,
        "recommendations": first.recommendations,
        "ward": first.ward,
        "post_discharge_advice": first.post_discharge_advice,
        "course_during_hospitalisation": first.course_during_hospitalisation,
        "medicine_injections_investigation": first.medicine_injections_investigation,
        "lab_results": lab_results,
        "medications": medications,
    }



# ---------------------------------------------------------------------------
# GET /api/normalization-report
# ---------------------------------------------------------------------------
@router.get("/normalization-report")
def normalization_report(session: Session = Depends(get_db)):
    """
    Show test names that could not be canonically mapped (no_match)
    to help tune the clinical name standardization config.
    """
    rows = session.execute(
        select(
            StandardizedRecord.test_name_original,
            func.count(StandardizedRecord.id).label("count"),
        )
        .where(
            StandardizedRecord.record_type == "lab_result",
            StandardizedRecord.normalization_method == "no_match",
        )
        .group_by(StandardizedRecord.test_name_original)
        .order_by(desc(func.count(StandardizedRecord.id)))
    ).all()

    return [{"test_name_original": r[0], "count": r[1]} for r in rows]


# ---------------------------------------------------------------------------
# Serializer helper
# ---------------------------------------------------------------------------
def _serialize_record(r: StandardizedRecord) -> dict:
    return {
        "id": r.id,
        "record_type": r.record_type,
        "filename": r.filename,
        "document_id": r.document_id,
        "trace_id": r.trace_id,
        "correlation_id": r.correlation_id,
        "claim_no": r.claim_no,
        "nt_code": r.nt_code,
        "source_system": r.source_system,
        "consumer_client_id": r.consumer_client_id,
        "patient_name": r.patient_name,
        "age": r.age,
        "gender": r.gender,
        "uhid": r.uhid,
        "hospital_name": r.hospital_name,
        "doctor_name": r.doctor_name,
        "bill_date": r.bill_date,
        "reports_date": r.reports_date,
        # Lab
        "test_name_canonical": r.test_name_canonical,
        "test_name_original": r.test_name_original,
        "result_value": r.result_value,
        "result_text": r.result_text,
        "unit_canonical": r.unit_canonical,
        "unit_original": r.unit_original,
        "range_low": r.range_low,
        "range_high": r.range_high,
        "range_text": r.range_text,
        "test_analytics": r.test_analytics,
        "classification": r.test_analytics,
        "normalization_method": r.normalization_method,
        "normalization_confidence": r.normalization_confidence,
        "page_no": r.page_no,
        # Discharge
        "admission_date": r.admission_date,
        "discharge_date": r.discharge_date,
        "diagnosis": r.diagnosis,
        "brief_history": r.brief_history,
        "recommendations": r.recommendations,
        "ward": r.ward,
        "medicine_injections_investigation": r.medicine_injections_investigation,
        # Medications
        "medicine": r.medicine,
        "dose": r.dose,
        "frequency": r.frequency,
        "medicine_type": r.medicine_type,
        # Audit
        "processed_at": r.processed_at.isoformat() if r.processed_at else None,
        "ingested_at": r.ingested_at.isoformat() if r.ingested_at else None,
    }
