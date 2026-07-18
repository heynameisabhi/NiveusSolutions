"""
Range Parser Utility

Parses range strings from lab reports into (range_low, range_high, range_text).

Handles formats:
    "4000-10000"      → (4000.0, 10000.0, "4000-10000")
    "1.5-4.5"         → (1.5,    4.5,     "1.5-4.5")
    "<50"             → (None,   50.0,    "<50")
    "≤50"             → (None,   50.0,    "≤50")
    ">100"            → (100.0,  None,    ">100")
    "150000-410000"   → (150000, 410000,  "150000-410000")
    "Less than 1:80"  → (None,   None,    "Less than 1:80")  [qualitative]
    "= 1 COI"         → (None,   None,    "= 1 COI")
    ""                → (None,   None,    "")
    "0-6"             → (0.0,    6.0,     "0-6")
    "8.0 - 23.0"      → (8.0,    23.0,    "8.0 - 23.0")
"""
from __future__ import annotations

import re

# Match "number - number" or "number–number" (with optional spaces)
_RANGE_PATTERN = re.compile(
    r'^([+-]?\d+(?:[.,]\d+)?(?:[eE][+-]?\d+)?)\s*[-–]\s*([+-]?\d+(?:[.,]\d+)?(?:[eE][+-]?\d+)?)$'
)

# Match "<number" or "≤number"
_LESS_THAN = re.compile(r'^[<≤]\s*([+-]?\d+(?:[.,]\d+)?)$')

# Match ">number" or "≥number"
_GREATER_THAN = re.compile(r'^[>≥]\s*([+-]?\d+(?:[.,]\d+)?)$')


def parse_range(range_str: str) -> tuple[float | None, float | None, str]:
    """
    Parse a range string into (range_low, range_high, range_text).
    Returns (None, None, original) for qualitative / unparseable ranges.
    """
    if not range_str:
        return None, None, range_str

    s = str(range_str).strip()
    range_text = s

    # Normalize comma decimals
    s_norm = s.replace(",", ".")

    m = _RANGE_PATTERN.match(s_norm)
    if m:
        return float(m.group(1)), float(m.group(2)), range_text

    m = _LESS_THAN.match(s_norm)
    if m:
        return None, float(m.group(1)), range_text

    m = _GREATER_THAN.match(s_norm)
    if m:
        return float(m.group(1)), None, range_text

    return None, None, range_text


def extract_result_value(result_str: str) -> tuple[float | None, str]:
    """
    Extract numeric value from result strings like:
        "91"             → (91.0, "91")
        "13.7 g/dl"      → (13.7, "13.7 g/dl")
        "4,290"          → (4290.0, "4,290")
        "POSITIVE"       → (None, "POSITIVE")
        "4,290 cells/cu.mm" → (4290.0, "4,290 cells/cu.mm")
    Returns (float_value, original_text).
    """
    if not result_str or not str(result_str).strip():
        return None, str(result_str)

    s = str(result_str).strip()
    result_text = s

    # 1. Clean thousands separator commas (e.g. "4,290" -> "4290")
    s_clean = re.sub(r'(?<=\d),(?=\d{3}(?:\D|$))', '', s)

    # 2. Search for the first numeric-like sequence
    m = re.search(r'([+-]?\d+(?:\.\d+)?)', s_clean)
    if m:
        try:
            return float(m.group(1)), result_text
        except ValueError:
            pass

    return None, result_text
