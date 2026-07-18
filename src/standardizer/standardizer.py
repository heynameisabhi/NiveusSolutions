"""
Standardizer Module — Clinical Name Normalization

Applies test name normalization using:
1. Exact match against canonical aliases (from test_mapping.json)
2. Fuzzy match via RapidFuzz if no exact match found
3. Falls back to storing original name with NULL canonical if confidence < threshold

Also handles:
- OCR artifact correction (e.g., "aemoglobin" → first letter dropped)
- Unit canonical mapping
"""
from __future__ import annotations

import logging
from typing import Any

from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)

# Fuzzy matching threshold (0-100). Below this → no canonical assigned.
FUZZY_THRESHOLD = 72.0

# Unit normalization map (raw → canonical)
UNIT_CANON: dict[str, str] = {
    "g/dl": "g/dL",
    "gm/dl": "g/dL",
    "g/l": "g/L",
    "mg/dl": "mg/dL",
    "mg/l": "mg/L",
    "u/l": "U/L",
    "iu/l": "IU/L",
    "mmol/l": "mmol/L",
    "umol/l": "umol/L",
    "nmol/l": "nmol/L",
    "pg/ml": "pg/mL",
    "ng/ml": "ng/mL",
    "ug/ml": "ug/mL",
    "cells/cu.mm": "cells/cu.mm",
    "cell/cu.mm": "cells/cu.mm",
    "million/cu.mm": "million/cu.mm",
    "mil/cu.mm": "million/cu.mm",
    "%": "%",
    "fl": "fL",
    "pg": "pg",
    "lac/cmm": "lac/cmm",
}


class ClinicalStandardizer:
    """
    Normalizes lab test names using exact-then-fuzzy matching.

    Args:
        test_mapping: dict of {canonical_name: [alias1, alias2, ...]}
    """

    def __init__(self, test_mapping: dict[str, list[str]]) -> None:
        self._canonical: list[str] = []
        # Build a flat lookup: lower(alias) → canonical
        self._exact_lookup: dict[str, str] = {}
        # All strings to match against for fuzzy: canonical + all aliases
        self._all_strings: list[str] = []
        self._string_to_canonical: dict[str, str] = {}

        for canonical, aliases in test_mapping.items():
            self._canonical.append(canonical)
            # Canonical name matches itself
            self._exact_lookup[canonical.lower().strip()] = canonical
            self._all_strings.append(canonical)
            self._string_to_canonical[canonical] = canonical

            for alias in aliases:
                alias_stripped = alias.strip()
                self._exact_lookup[alias_stripped.lower()] = canonical
                self._all_strings.append(alias_stripped)
                self._string_to_canonical[alias_stripped] = canonical

    def normalize_test_name(
        self, test_name_original: str
    ) -> tuple[str | None, str, float]:
        """
        Normalize a test name.

        Returns:
            (canonical_name, method, confidence)
            method: "exact_match" | "fuzzy_match" | "no_match"
            confidence: 0.0–1.0
        """
        if not test_name_original:
            return None, "no_match", 0.0

        cleaned = test_name_original.strip()
        lower = cleaned.lower()

        # 1. Exact match (case-insensitive)
        if lower in self._exact_lookup:
            return self._exact_lookup[lower], "exact_match", 1.0

        # 2. Fuzzy match
        if self._all_strings:
            result = process.extractOne(
                cleaned,
                self._all_strings,
                scorer=fuzz.token_sort_ratio,
                score_cutoff=FUZZY_THRESHOLD,
            )
            if result is not None:
                matched_str, score, _ = result
                canonical = self._string_to_canonical[matched_str]
                return canonical, "fuzzy_match", round(score / 100.0, 4)

        # 3. No match
        return None, "no_match", 0.0

    def normalize_unit(self, unit: str) -> str:
        """Normalize a unit string to canonical form."""
        if not unit:
            return unit
        return UNIT_CANON.get(unit.strip().lower(), unit.strip())


def standardize_records(
    records: list[dict],
    standardizer: ClinicalStandardizer,
) -> list[dict]:
    """
    Apply test name and unit normalization to all lab_result rows.
    Discharge medication rows are passed through unchanged.

    Modifies records in-place and returns them.
    """
    from src.parser.parser import RECORD_TYPE_LAB
    from src.validator.validator import classify_result

    for rec in records:
        if rec.get("record_type") != RECORD_TYPE_LAB:
            continue

        original = rec.get("test_name_original") or ""
        canonical, method, confidence = standardizer.normalize_test_name(original)

        rec["test_name_canonical"] = canonical
        rec["normalization_method"] = method
        rec["normalization_confidence"] = confidence

        # Unit normalization
        raw_unit = rec.get("unit_original") or ""
        rec["unit_canonical"] = standardizer.normalize_unit(raw_unit)

        # Run range classification and save in test_analytics
        rec["test_analytics"] = classify_result(
            rec.get("result_value"),
            rec.get("range_low"),
            rec.get("range_high"),
            rec.get("result_text"),
        )

    return records
