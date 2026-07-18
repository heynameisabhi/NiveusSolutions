"""
Unit tests for the Standardizer module (Real Schema/Real Data Pipeline).
"""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.utils.range_parser import parse_range, extract_result_value
from src.standardizer.standardizer import ClinicalStandardizer, standardize_records


# ---------------------------------------------------------------------------
# Range Parsing Tests
# ---------------------------------------------------------------------------
class TestParseRange:
    def test_simple_range(self):
        low, high, txt = parse_range("4000-10000")
        assert low == 4000.0
        assert high == 10000.0
        assert txt == "4000-10000"

    def test_decimal_range(self):
        low, high, txt = parse_range("4.50-5.50")
        assert low == 4.5
        assert high == 5.5

    def test_less_than(self):
        low, high, txt = parse_range("<50")
        assert low is None
        assert high == 50.0

    def test_greater_than(self):
        low, high, txt = parse_range(">100")
        assert low == 100.0
        assert high is None

    def test_qualitative_range(self):
        low, high, txt = parse_range("Less than 1:80")
        assert low is None
        assert high is None
        assert txt == "Less than 1:80"


# ---------------------------------------------------------------------------
# Result Value Extraction Tests
# ---------------------------------------------------------------------------
class TestExtractResultValue:
    def test_numeric_only(self):
        val, txt = extract_result_value("91")
        assert val == 91.0
        assert txt == "91"

    def test_decimal_with_unit(self):
        val, txt = extract_result_value("13.7 g/dl")
        assert val == 13.7
        assert txt == "13.7 g/dl"

    def test_with_commas(self):
        val, txt = extract_result_value("4,290 cells/cu.mm")
        assert val == 4290.0
        assert txt == "4,290 cells/cu.mm"

    def test_qualitative_result(self):
        val, txt = extract_result_value("POSITIVE")
        assert val is None
        assert txt == "POSITIVE"


# ---------------------------------------------------------------------------
# Clinical Test Name Normalization Tests
# ---------------------------------------------------------------------------
class TestClinicalStandardizer:
    TEST_MAPPING = {
        "HAEMOGLOBIN": ["Haemoglobin", "Hb", "HGB", "aemoglobin", "hemoglobin"],
        "WHITE BLOOD CELL COUNT": ["TOTAL WBC COUNT", "Total WBC Count", "WBC COUNT", "tal WBC Count"],
    }

    @pytest.fixture
    def standardizer(self):
        return ClinicalStandardizer(self.TEST_MAPPING)

    def test_exact_match(self, standardizer):
        canon, method, conf = standardizer.normalize_test_name("Hb")
        assert canon == "HAEMOGLOBIN"
        assert method == "exact_match"
        assert conf == 1.0

    def test_exact_match_case_insensitive(self, standardizer):
        canon, method, conf = standardizer.normalize_test_name("haemoglobin")
        assert canon == "HAEMOGLOBIN"
        assert method == "exact_match"
        assert conf == 1.0

    def test_fuzzy_match_ocr_artifact(self, standardizer):
        # "aemoglobin" is in the alias list so it is an exact match actually.
        # Let's test a true fuzzy match like "haemoglob"
        canon, method, conf = standardizer.normalize_test_name("haemoglob")
        assert canon == "HAEMOGLOBIN"
        assert method == "fuzzy_match"
        assert conf > 0.7

    def test_no_match(self, standardizer):
        canon, method, conf = standardizer.normalize_test_name("random test")
        assert canon is None
        assert method == "no_match"
        assert conf == 0.0

    def test_unit_canonicalization(self, standardizer):
        assert standardizer.normalize_unit("g/dl") == "g/dL"
        assert standardizer.normalize_unit("mil/cu.mm") == "million/cu.mm"
        assert standardizer.normalize_unit("unknown") == "unknown"


# ---------------------------------------------------------------------------
# Full Standardize Integration Tests
# ---------------------------------------------------------------------------
def test_standardize_records_integration():
    test_mapping = {
        "HAEMOGLOBIN": ["Hb"],
    }
    std = ClinicalStandardizer(test_mapping)
    records = [
        {
            "record_type": "lab_result",
            "test_name_original": "Hb",
            "result_value": 13.7,
            "result_text": "13.7 g/dl",
            "unit_original": "g/dl",
            "range_low": 13.0,
            "range_high": 17.0,
        },
        {
            "record_type": "discharge_medication",
            "medicine": "Tab. miso",
        }
    ]

    standardize_records(records, std)

    # Check lab result updated
    lab = records[0]
    assert lab["test_name_canonical"] == "HAEMOGLOBIN"
    assert lab["normalization_method"] == "exact_match"
    assert lab["unit_canonical"] == "g/dL"
    assert lab["test_analytics"] == "Within Range"

    # Check medication unchanged
    med = records[1]
    assert "test_name_canonical" not in med
