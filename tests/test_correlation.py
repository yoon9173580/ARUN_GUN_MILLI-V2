"""Unit tests for Layer 4 — Correlation / Market Microstructure.

Covers:
- Full sector sync (all up or all down) → max score 20
- QQQ divergence penalty
- IWM risk-on/off (small caps)
- Missing data tolerance
- Score capped at [0, 20]
"""
import pytest

from engines.correlation import calculate_correlation_score


class TestFullAlignment:
    def test_all_aligned_up_max_score(self):
        # SPY+QQQ+IWM all up, with DIA also up — fully aligned
        pcts = {"SPY": 0.50, "QQQ": 0.40, "IWM": 0.93, "DIA": 0.61}
        result = calculate_correlation_score(pcts)
        # QQQ:10 + IWM:5 (>0.3) + Sync:5 + DIA:3 = 23 → capped 20
        assert result["score"] == 20
        assert result["max"] == 20
        assert result["sector_sync"] is True

    def test_all_aligned_down_full_sync(self):
        pcts = {"SPY": -0.50, "QQQ": -0.40, "IWM": -0.93, "DIA": -0.61}
        result = calculate_correlation_score(pcts)
        # QQQ:10 + IWM:-3 + Sync:5 + DIA:3 = 15
        assert result["score"] == 15
        assert result["sector_sync"] is True

    def test_qqq_divergence_penalty(self):
        # SPY up but QQQ down → -5
        pcts = {"SPY": 0.30, "QQQ": -0.10, "IWM": 0.40, "DIA": 0.20}
        result = calculate_correlation_score(pcts)
        # QQQ:-5 + IWM:5 + Sync:0 (QQQ broken) + DIA:3 = 3
        assert result["score"] == 3
        assert result["sector_sync"] is False


class TestIWMRiskOnOff:
    def test_iwm_risk_on_threshold(self):
        # IWM > 0.3 → +5
        pcts = {"SPY": 0.20, "QQQ": 0.20, "IWM": 0.31, "DIA": 0.20}
        result = calculate_correlation_score(pcts)
        # Includes 5 from IWM risk-on
        assert result["details"]["iwm_risk"]["score"] == 5

    def test_iwm_risk_off_penalty(self):
        # IWM < -0.3 → -3
        pcts = {"SPY": -0.40, "QQQ": -0.40, "IWM": -0.50, "DIA": -0.20}
        result = calculate_correlation_score(pcts)
        assert result["details"]["iwm_risk"]["score"] == -3

    def test_iwm_neutral_zone(self):
        pcts = {"SPY": 0.10, "QQQ": 0.10, "IWM": 0.10, "DIA": 0.10}
        result = calculate_correlation_score(pcts)
        assert result["details"]["iwm_risk"]["score"] == 0
        assert "Neutral" in result["details"]["iwm_risk"]["detail"]


class TestMissingData:
    def test_missing_qqq_zero_score_no_crash(self):
        pcts = {"SPY": 0.30, "QQQ": None, "IWM": 0.40, "DIA": 0.20}
        result = calculate_correlation_score(pcts)
        assert result["details"]["qqq_alignment"]["score"] == 0
        assert "unavailable" in result["details"]["qqq_alignment"]["detail"]

    def test_missing_iwm_zero_score(self):
        pcts = {"SPY": 0.30, "QQQ": 0.20, "IWM": None, "DIA": 0.10}
        result = calculate_correlation_score(pcts)
        assert result["details"]["iwm_risk"]["score"] == 0
        # Sector sync also fails since IWM is None
        assert result["details"]["sector_sync"]["score"] == 0

    def test_missing_dia_no_crash(self):
        pcts = {"SPY": 0.30, "QQQ": 0.20, "IWM": 0.40, "DIA": None}
        result = calculate_correlation_score(pcts)
        assert result["details"]["dia_alignment"]["score"] == 0

    def test_all_missing_returns_zero(self):
        pcts = {"SPY": None, "QQQ": None, "IWM": None, "DIA": None}
        result = calculate_correlation_score(pcts)
        assert result["score"] == 0


class TestScoreCapping:
    def test_score_capped_at_20(self):
        # Best possible inputs
        pcts = {"SPY": 1.0, "QQQ": 1.0, "IWM": 1.0, "DIA": 1.0}
        result = calculate_correlation_score(pcts)
        assert result["score"] <= 20

    def test_score_floored_at_zero(self):
        # Worst case mix that would otherwise go negative
        pcts = {"SPY": 0.5, "QQQ": -0.5, "IWM": -1.0, "DIA": -0.3}
        result = calculate_correlation_score(pcts)
        assert result["score"] >= 0


class TestReturnShape:
    def test_required_keys(self):
        pcts = {"SPY": 0.30, "QQQ": 0.20, "IWM": 0.40, "DIA": 0.10}
        result = calculate_correlation_score(pcts)
        assert {"score", "max", "sector_sync", "details"}.issubset(result.keys())
        assert {"qqq_alignment", "iwm_risk", "sector_sync", "dia_alignment"}.issubset(
            result["details"].keys()
        )
