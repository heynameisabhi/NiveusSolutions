"""
Validator Module — Veritas Claims Range Classification

Classifies lab results based on parsed numeric values and ranges:
    - Within Range
    - Above Range
    - Below Range
    - Outlier
    - Invalid
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

WITHIN_RANGE = "Within Range"
ABOVE_RANGE = "Above Range"
BELOW_RANGE = "Below Range"
OUTLIER = "Outlier"
INVALID = "Invalid"

FLAGGED_CLASSIFICATIONS = {ABOVE_RANGE, BELOW_RANGE, OUTLIER, INVALID}


def classify_result(
    result_value: float | None,
    range_low: float | None,
    range_high: float | None,
    result_text: str | None = None,
) -> str:
    """
    Classify a result value relative to parsed low/high reference boundaries.
    """
    if result_value is None:
        # If there are reference bounds but no numeric value, it's invalid/missing
        if range_low is not None or range_high is not None:
            return INVALID

        # Handle qualitative results that indicate abnormalities
        if result_text:
            text_upper = str(result_text).strip().upper()
            if text_upper in ("POSITIVE", "REACTIVE", "DETECTED", "HIGH"):
                return ABOVE_RANGE
            if text_upper in ("NEGATIVE", "NON-REACTIVE", "NOT DETECTED", "NORMAL", "NIL"):
                return WITHIN_RANGE

        return WITHIN_RANGE

    # Outlier detection: more than 3x the range width outside boundaries
    if range_low is not None and range_high is not None:
        width = range_high - range_low
        if width > 0:
            if result_value > range_high + 3 * width or result_value < range_low - 3 * width:
                return OUTLIER

    if range_high is not None and result_value > range_high:
        return ABOVE_RANGE

    if range_low is not None and result_value < range_low:
        return BELOW_RANGE

    return WITHIN_RANGE
