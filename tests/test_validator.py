"""
Unit tests for the Validator module (classify_result function).
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.validator.validator import (
    classify_result,
    WITHIN_RANGE, ABOVE_RANGE, BELOW_RANGE, OUTLIER, INVALID
)


class TestClassifyResult:
    def test_within_range(self):
        assert classify_result(14.5, 13.5, 17.5) == WITHIN_RANGE
        assert classify_result(85.0, 70.0, 100.0) == WITHIN_RANGE

    def test_above_range(self):
        assert classify_result(18.0, 13.5, 17.5) == ABOVE_RANGE
        assert classify_result(110.0, 70.0, 100.0) == ABOVE_RANGE

    def test_below_range(self):
        assert classify_result(12.0, 13.5, 17.5) == BELOW_RANGE
        assert classify_result(50.0, 70.0, 100.0) == BELOW_RANGE

    def test_outlier(self):
        # range 70-100 (width=30). Outlier if > 100 + 3*30 = 190, or < 70 - 3*30 = -20
        assert classify_result(210.0, 70.0, 100.0) == OUTLIER
        assert classify_result(500.0, 70.0, 100.0) == OUTLIER

    def test_invalid(self):
        assert classify_result(None, 13.5, 17.5) == INVALID

    def test_qualitative_positive(self):
        assert classify_result(None, None, None, "POSITIVE") == ABOVE_RANGE
        assert classify_result(None, None, None, "detected") == ABOVE_RANGE

    def test_qualitative_negative(self):
        assert classify_result(None, None, None, "NEGATIVE") == WITHIN_RANGE
        assert classify_result(None, None, None, "not detected") == WITHIN_RANGE
