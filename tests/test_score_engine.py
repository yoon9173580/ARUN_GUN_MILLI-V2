"""Unit tests for Layer 0 — Signal Grade & Score Engine Orchestration.

Covers:
- Signal grade mapping (NONE / WEAK / MODERATE / STRONG)
- Threshold boundary conditions
- Grade fields completeness
"""
import os
import pytest

from engines.score_engine import (
    determine_signal_grade,
    GRADE_STRONG,
    GRADE_MODERATE,
    GRADE_WEAK,
)


class TestSignalGradeThresholds:
    def test_strong_grade_at_threshold(self):
        result = determine_signal_grade(GRADE_STRONG)
        assert result["grade"] == "STRONG"
        assert result["label"] == "STRONG SIGNAL"

    def test_strong_grade_above_threshold(self):
        result = determine_signal_grade(100)
        assert result["grade"] == "STRONG"

    def test_moderate_grade_at_threshold(self):
        result = determine_signal_grade(GRADE_MODERATE)
        assert result["grade"] == "MODERATE"

    def test_moderate_below_strong(self):
        result = determine_signal_grade(GRADE_STRONG - 1)
        assert result["grade"] == "MODERATE"

    def test_weak_grade_at_threshold(self):
        result = determine_signal_grade(GRADE_WEAK)
        assert result["grade"] == "WEAK"
        assert result["label"] == "STANDBY"

    def test_none_below_weak(self):
        result = determine_signal_grade(GRADE_WEAK - 1)
        assert result["grade"] == "NONE"
        assert result["label"] == "NO SIGNAL"

    def test_zero_score_returns_none(self):
        result = determine_signal_grade(0)
        assert result["grade"] == "NONE"

    def test_negative_score_returns_none(self):
        result = determine_signal_grade(-50)
        assert result["grade"] == "NONE"


class TestSignalGradeShape:
    @pytest.mark.parametrize("score", [0, 50, 75, 90, 100])
    def test_returns_required_keys(self, score):
        result = determine_signal_grade(score)
        required = {"grade", "label", "emoji", "action", "color"}
        assert required.issubset(set(result.keys()))

    @pytest.mark.parametrize("score", [0, 50, 75, 90, 100])
    def test_color_is_hex(self, score):
        result = determine_signal_grade(score)
        assert result["color"].startswith("#")
        assert len(result["color"]) == 7  # #rrggbb

    def test_strong_color_green(self):
        result = determine_signal_grade(95)
        assert result["color"] == "#3dd68c"  # green

    def test_none_color_red(self):
        result = determine_signal_grade(10)
        assert result["color"] == "#f07178"  # red


class TestGradeOrdering:
    """Ensure thresholds maintain strict ordering."""

    def test_thresholds_strictly_increasing(self):
        assert GRADE_WEAK < GRADE_MODERATE < GRADE_STRONG

    def test_no_overlap_between_grades(self):
        # Score that's MODERATE should not be STRONG, etc.
        mod_top = determine_signal_grade(GRADE_STRONG - 1)
        weak_top = determine_signal_grade(GRADE_MODERATE - 1)
        none_top = determine_signal_grade(GRADE_WEAK - 1)
        assert mod_top["grade"] == "MODERATE"
        assert weak_top["grade"] == "WEAK"
        assert none_top["grade"] == "NONE"
