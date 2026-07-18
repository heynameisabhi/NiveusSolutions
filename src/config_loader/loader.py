"""
Config Loader — loads JSON/YAML config files from the config/ directory.

Provides lazy-cached access to:
    - test_mapping.json       → canonical clinical name map
    - unit_mapping.json       → unit conversion factors
    - medicine_mapping.json   → drug brand → generic
    - reference_ranges.json   → lab reference ranges (for flagging)
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).parent.parent.parent / "config"


def _load_json(filename: str) -> dict:
    path = CONFIG_DIR / filename
    if not path.exists():
        logger.warning("Config file not found: %s", path)
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def get_test_mapping() -> dict[str, list[str]]:
    """canonical_name → [alias1, alias2, ...]"""
    return _load_json("test_mapping.json")


@lru_cache(maxsize=1)
def get_unit_mapping() -> dict:
    return _load_json("unit_mapping.json")


@lru_cache(maxsize=1)
def get_medicine_mapping() -> dict:
    return _load_json("medicine_mapping.json")


@lru_cache(maxsize=1)
def get_reference_ranges() -> dict:
    return _load_json("reference_ranges.json")


def reload_all() -> None:
    """Clear all caches (useful for testing)."""
    get_test_mapping.cache_clear()
    get_unit_mapping.cache_clear()
    get_medicine_mapping.cache_clear()
    get_reference_ranges.cache_clear()
