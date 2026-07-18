"""
Ingestion Module — Veritas Claims API Format

Parses the real Veritas API response wrapper:
{
  "traceId": "...",
  "data": {
    "documentId": "DOC01...",
    "correlationId": "...",
    "metaDetails": [{"key": "claim_no", "value": "..."}, ...],
    "responseDetails": [
      {"classifier": "lab_report",         "data": {...}},
      {"classifier": "discharge_summary",  "data": {...}}
    ]
  }
}

Responsibilities:
- Scan folder for JSON files
- Validate they are valid Veritas API responses
- Extract top-level metadata
- Compute content hash for dedup
- Separate files by document type
"""
from __future__ import annotations

import hashlib
import json
import logging
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class VeritasDocument:
    """Parsed top-level Veritas document with metadata extracted."""
    filename: str
    raw_json: str
    trace_id: str
    document_id: str
    correlation_id: str
    meta: dict[str, str]          # flattened metaDetails
    response_details: list[dict]  # list of {classifier, data, status, ...}
    report_hash: str


@dataclass
class IngestionResult:
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    documents: list[VeritasDocument] = field(default_factory=list)
    failed: list[dict] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.documents) + len(self.failed)


def _compute_hash(data: dict) -> str:
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=True)
    return hashlib.md5(canonical.encode()).hexdigest()


def _extract_meta(meta_list: list[dict]) -> dict[str, str]:
    """Flatten [{key, value}] → {key: value}."""
    return {item.get("key", ""): item.get("value", "") for item in meta_list if item.get("key")}


def _is_veritas_format(data: dict) -> bool:
    """Check that this is a valid Veritas API response."""
    return (
        isinstance(data, dict)
        and "data" in data
        and isinstance(data.get("data"), dict)
        and "responseDetails" in data["data"]
    )


def scan_folder(folder: str | Path) -> IngestionResult:
    """
    Scan *folder* for *.json files and return IngestionResult.

    Each file is validated as a Veritas API response.
    Failed files are logged and tracked but do not abort the batch.
    """
    folder = Path(folder)
    result = IngestionResult()

    if not folder.exists():
        logger.error("Ingest folder does not exist: %s", folder)
        return result

    json_files = list(folder.glob("*.json"))
    logger.info("Found %d JSON file(s) in %s", len(json_files), folder)

    for json_path in json_files:
        try:
            raw_text = json_path.read_text(encoding="utf-8")
            data: dict = json.loads(raw_text)

            if not _is_veritas_format(data):
                raise ValueError(
                    "File is not a valid Veritas API response "
                    "(missing data.responseDetails)"
                )

            doc_data: dict = data.get("data", {})

            # Check status
            if data.get("statusCode", 200) != 200:
                raise ValueError(f"API response has non-200 status: {data.get('statusCode')}")

            # Check at least one successful responseDetail
            details = doc_data.get("responseDetails", [])
            successful = [d for d in details if d.get("status") == "success"]
            if not successful:
                raise ValueError("No successful responseDetails in document")

            doc = VeritasDocument(
                filename=json_path.name,
                raw_json=raw_text,
                trace_id=data.get("traceId", ""),
                document_id=doc_data.get("documentId", ""),
                correlation_id=doc_data.get("correlationId", ""),
                meta=_extract_meta(doc_data.get("metaDetails", [])),
                response_details=details,
                report_hash=_compute_hash(data),
            )
            result.documents.append(doc)
            logger.debug(
                "Ingested: %s (doc=%s, classifiers=%s)",
                json_path.name,
                doc.document_id,
                [d.get("classifier") for d in details],
            )

        except (json.JSONDecodeError, ValueError, OSError) as exc:
            logger.warning("Failed to ingest %s: %s", json_path.name, exc)
            result.failed.append({"filename": json_path.name, "error": str(exc)})

    return result
