"""
Parser Module — Veritas Claims API

Converts a VeritasDocument into a list of flat record dicts,
one per test result (lab_report) or per medication (discharge_summary).

Each record dict maps directly to StandardizedRecord columns.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from src.ingestion.ingestion import VeritasDocument
from src.utils.range_parser import extract_result_value, parse_range

logger = logging.getLogger(__name__)

RECORD_TYPE_LAB = "lab_result"
RECORD_TYPE_MED = "discharge_medication"
RECORD_TYPE_DISCHARGE = "discharge_summary"


def _build_common(doc: VeritasDocument) -> dict:
    """Build the fields that are common to every row from this document."""
    return {
        "filename": doc.filename,
        "document_id": doc.document_id,
        "trace_id": doc.trace_id,
        "correlation_id": doc.correlation_id,
        "source_system": doc.meta.get("source_system"),
        "claim_no": doc.meta.get("claim_no"),
        "nt_code": doc.meta.get("nt_code"),
        "consumer_client_id": doc.meta.get("ConsumerClientId"),
        "destination_identifier": doc.meta.get("DestinationIdentifier"),
        "metadetails": json.dumps(doc.meta),
    }


def parse_lab_report(detail_data: dict, common: dict) -> list[dict]:
    """
    Parse a lab_report responseDetail into one row per test result.
    """
    rows: list[dict] = []
    basic: dict = detail_data.get("basic_info", {})
    report_details: list[dict] = detail_data.get("report_details", [])

    # Patient context from basic_info
    patient_ctx = {
        "patient_name": basic.get("patient_name"),
        "age": basic.get("age"),
        "gender": basic.get("gender"),
        "uhid": basic.get("uhid"),
        "lab_or_hospital_name": basic.get("lab_or_hospital_name"),
        "hospital_name": basic.get("lab_or_hospital_name"),  # populate both
        "bill_date": basic.get("bill_date"),
        "reports_date": basic.get("reports_date"),
    }

    for test in report_details:
        test_name_raw: str = str(test.get("test_name", "")).strip()
        result_raw: str = str(test.get("result", "")).strip()
        unit_raw: str = str(test.get("unit", "")).strip()
        range_raw: str = str(test.get("range", "")).strip()
        analytics: str = str(test.get("test_analytics", "")).strip()
        page_no: Any = test.get("page_no")

        # Skip header/placeholder rows
        if test_name_raw.lower() in ("test_name", "", "n/a"):
            continue
        if result_raw.lower() in ("result", "n/a", "low/normal/high"):
            continue

        # Parse range
        range_low, range_high, range_text = parse_range(range_raw)

        # Extract numeric result
        result_value, result_text = extract_result_value(result_raw)

        row = {
            **common,
            **patient_ctx,
            "record_type": RECORD_TYPE_LAB,
            "test_name_original": test_name_raw,
            "test_name_canonical": None,       # filled by standardizer
            "result_value": result_value,
            "result_text": result_text,
            "unit_original": unit_raw,
            "unit_canonical": unit_raw,        # unit normalization TBD
            "range_low": range_low,
            "range_high": range_high,
            "range_text": range_text,
            "test_analytics": analytics,
            "page_no": str(page_no) if page_no is not None else None,
            "normalization_method": None,
            "normalization_confidence": None,
        }
        rows.append(row)

    logger.debug(
        "lab_report parsed: %d test rows from %s",
        len(rows), common.get("filename"),
    )
    return rows


def parse_discharge_summary(detail_data: dict, common: dict) -> list[dict]:
    """
    Parse a discharge_summary responseDetail.
    Returns:
      - One row per discharge medication (record_type = 'discharge_medication')
      - If no medications, one row for the summary header (record_type = 'discharge_summary')
    All rows carry the full discharge context (diagnosis, dates, etc.).
    """
    rows: list[dict] = []

    discharge_ctx = {
        "patient_name": detail_data.get("patientName"),
        "age": detail_data.get("age"),
        "gender": detail_data.get("gender"),
        "hospital_name": detail_data.get("hospitalName"),
        "hospital_address": detail_data.get("hospitalAddress"),
        "doctor_name": detail_data.get("doctorName"),
        "admission_date": detail_data.get("admissionDate"),
        "discharge_date": detail_data.get("dischargeDate"),
        "diagnosis": detail_data.get("diagnosis"),
        "brief_history": detail_data.get("briefHistory"),
        "general_examinations": detail_data.get("generalExaminations"),
        "recommendations": detail_data.get("recommendations"),
        "ward": detail_data.get("ward"),
        "post_discharge_advice": detail_data.get("postDischargeAdvice"),
        "course_during_hospitalisation": json.dumps(
            detail_data.get("courseDuringHospitalisation") or []
        ),
        "medicine_injections_investigation": json.dumps(
            detail_data.get("medicineInjectionsInvestigation") or []
        ),
    }

    medications: list[dict] = detail_data.get("dischargeMedications", []) or []

    # Filter out clearly blank/N/A entries
    valid_meds = [
        m for m in medications
        if m.get("medicine") and str(m.get("medicine", "")).strip().upper() not in ("", "N/A")
    ]

    if valid_meds:
        for med in valid_meds:
            row = {
                **common,
                **discharge_ctx,
                "record_type": RECORD_TYPE_MED,
                "medicine": str(med.get("medicine", "")).strip(),
                "dose": str(med.get("dose", "")).strip() or None,
                "frequency": str(med.get("frequency", "")).strip() or None,
                "medicine_type": str(med.get("type", "")).strip() or None,
            }
            rows.append(row)
    else:
        # Summary-only row
        row = {
            **common,
            **discharge_ctx,
            "record_type": RECORD_TYPE_DISCHARGE,
            "medicine": None,
            "dose": None,
            "frequency": None,
            "medicine_type": None,
        }
        rows.append(row)

    logger.debug(
        "discharge_summary parsed: %d rows from %s",
        len(rows), common.get("filename"),
    )
    return rows


def parse_document(doc: VeritasDocument) -> list[dict]:
    """
    Parse a full VeritasDocument into a flat list of record dicts.
    Handles documents with mixed lab_report + discharge_summary classifiers.
    """
    common = _build_common(doc)
    all_rows: list[dict] = []

    for response_detail in doc.response_details:
        if response_detail.get("status") != "success":
            continue

        classifier: str = response_detail.get("classifier", "")
        detail_data: dict = response_detail.get("data") or {}

        if classifier == "lab_report":
            rows = parse_lab_report(detail_data, common)
            all_rows.extend(rows)
        elif classifier == "discharge_summary":
            rows = parse_discharge_summary(detail_data, common)
            all_rows.extend(rows)
        else:
            logger.warning(
                "Unknown classifier '%s' in %s — skipping",
                classifier, doc.filename,
            )

    logger.info(
        "Parsed %s: %d total rows (%d classifiers)",
        doc.filename, len(all_rows), len(doc.response_details),
    )
    return all_rows
