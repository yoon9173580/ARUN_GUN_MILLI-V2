"""Unit tests for Layer 5 — Time Window Filter.

Covers:
- PRIME window (10:30-11:30) scores max
- LUNCH_LULL blocks entries
- Friday adjustment (-5)
- Pre-market / after-hours return 0
- next_window countdown correctness
"""
import pytest
from datetime import datetime
import pytz

from engines.time_window import calculate_time_score


NY = pytz.timezone("America/New_York")


def et(hour, minute, weekday_offset=0):
    """Build a tz-aware ET datetime for a given hour/minute (Tuesday default)."""
    # 2024-01-02 is Tuesday — use it as base, add weekday_offset for other days
    base = datetime(2024, 1, 2 + weekday_offset, hour, minute)
    return NY.localize(base)


class TestWindowScoring:
    def test_prime_window_max_score(self):
        # 10:30 = 630 min → PRIME (score 20)
        result = calculate_time_score(et(10, 30))
        assert result["window"] == "PRIME"
        assert result["score"] == 20
        assert result["max"] == 20
        assert result["is_blocked"] is False
        assert result["emoji"] == "🟢"

    def test_prime_window_end(self):
        # 11:29 still PRIME
        result = calculate_time_score(et(11, 29))
        assert result["window"] == "PRIME"
        assert result["score"] == 20

    def test_lunch_lull_blocks(self):
        # 12:30 = 750 min → LUNCH_LULL (score 0, blocked)
        result = calculate_time_score(et(12, 30))
        assert result["window"] == "LUNCH_LULL"
        assert result["score"] == 0
        assert result["is_blocked"] is True

    def test_gamma_window(self):
        # 14:30 = 870 min → GAMMA (score 15)
        result = calculate_time_score(et(14, 30))
        assert result["window"] == "GAMMA"
        assert result["score"] == 15

    def test_gamma_bomb_blocks(self):
        # 15:00 = 900 min → GAMMA_BOMB (score 0, blocked)
        result = calculate_time_score(et(15, 0))
        assert result["window"] == "GAMMA_BOMB"
        assert result["score"] == 0
        assert result["is_blocked"] is True

    def test_open_chaos_blocks(self):
        # 09:35 = 575 min → OPEN_CHAOS (score 0, blocked)
        result = calculate_time_score(et(9, 35))
        assert result["window"] == "OPEN_CHAOS"
        assert result["score"] == 0
        assert result["is_blocked"] is True

    def test_pre_market_returns_zero(self):
        # 8:00 = before market open, no window matches → score 0, label CLOSED
        result = calculate_time_score(et(8, 0))
        assert result["score"] == 0
        assert result["window"] == "CLOSED"
        # is_blocked is False outside windows (no avoid behavior pre-market)

    def test_after_close_returns_zero(self):
        # 17:00 = after close
        result = calculate_time_score(et(17, 0))
        assert result["score"] == 0
        assert result["window"] == "CLOSED"


class TestDayBias:
    def test_friday_adjustment_minus_five(self):
        # Friday PRIME: 20 - 5 = 15
        # weekday_offset=3 → Tue + 3 = Friday
        result = calculate_time_score(et(10, 30, weekday_offset=3))
        assert result["day_bias"]["label"] == "Friday"
        assert result["day_bias"]["adj"] == -5
        assert result["score"] == 15  # 20 - 5

    def test_monday_no_adjustment(self):
        # 2024-01-01 was Monday — use offset -1 from Tue base
        result = calculate_time_score(et(10, 30, weekday_offset=-1))
        assert result["day_bias"]["label"] == "Monday"
        assert result["day_bias"]["adj"] == 0
        assert result["score"] == 20  # unmodified PRIME

    def test_score_never_negative(self):
        # Friday in zero-score window: 0 + (-5) capped at 0
        result = calculate_time_score(et(12, 30, weekday_offset=3))
        assert result["score"] == 0  # max(0, 0 + -5) = 0


class TestNextWindow:
    def test_lunch_shows_next_gamma(self):
        # 12:30 LUNCH_LULL → next good window = GAMMA at 14:00 (= 840 min)
        result = calculate_time_score(et(12, 30))
        nw = result["next_window"]
        assert nw is not None
        assert nw["window"] == "GAMMA"
        assert nw["starts_at"] == "14:00"
        assert nw["minutes_until"] == 90  # 840 - 750
        assert nw["countdown"] == "1h 30m"

    def test_prime_no_next_window(self):
        # In PRIME already (score 20) → no next_window needed
        result = calculate_time_score(et(10, 30))
        # Implementation: next_window only set when score < 15
        assert result["next_window"] is None

    def test_open_chaos_shows_prime_next(self):
        # 09:35 OPEN_CHAOS → next prime is PRIME at 10:30 (630)
        result = calculate_time_score(et(9, 35))
        nw = result["next_window"]
        assert nw is not None
        # First window with score >= 15 after 09:35 = PRIME @ 10:30
        assert nw["window"] == "PRIME"


class TestReturnShape:
    def test_returns_all_keys(self):
        result = calculate_time_score(et(10, 30))
        required = {
            "score", "max", "window", "emoji", "description",
            "day_bias", "next_window", "is_blocked", "current_time",
        }
        assert required.issubset(set(result.keys()))

    def test_current_time_formatted(self):
        result = calculate_time_score(et(10, 30))
        assert result["current_time"] == "10:30"
