"""
Test per `_compute_priority_score_v1_basic` — contratto DL-ARCH-V2-044, TASK-V2-149.

Copertura:
- time_urgency: fasce step-function (<= 7, 15, 30, 60, > 60, None)
- customer_pressure: fasce shortage_qty (> 0, >= 100, >= 500, >= 1000), cap 40
- stock_pressure: ratio-based (>= 1.0, 0.75-1, 0.50-0.75, 0.25-0.50, 0-0.25, < 0)
  - nessuna pressione se replenishment <= 0 o target <= 0
- release_penalty: launchable_now, launchable_partially, blocked_by_capacity_now, None
- warning_penalty: 0, 1, 2-3, >= 4 warning
- clamp 0..100 (score non puo andare negativo)
- priority_band derivata da score (low / medium / high / critical)
- guardrail: customer pesa piu di stock su casi comparabili
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from nssp_v2.core.planning_candidates.queries import _compute_priority_score_v1_basic


# ─── Helper ──────────────────────────────────────────────────────────────────

def compute(
    *,
    days_ahead: int | None = None,
    customer_shortage_qty: float | None = None,
    stock_replenishment_qty: float | None = None,
    stock_effective_qty: float | None = None,
    target_stock_qty: float | None = None,
    release_status: str | None = None,
    active_warnings_count: int = 0,
) -> tuple[float, str]:
    """Wrapper per semplificare i test — converte float -> Decimal e days_ahead -> date."""
    today = date.today()
    nearest = today + timedelta(days=days_ahead) if days_ahead is not None else None
    return _compute_priority_score_v1_basic(
        nearest_delivery_date=nearest,
        customer_shortage_qty=Decimal(str(customer_shortage_qty)) if customer_shortage_qty is not None else None,
        stock_replenishment_qty=Decimal(str(stock_replenishment_qty)) if stock_replenishment_qty is not None else None,
        stock_effective_qty=Decimal(str(stock_effective_qty)) if stock_effective_qty is not None else None,
        target_stock_qty=Decimal(str(target_stock_qty)) if target_stock_qty is not None else None,
        release_status=release_status,
        active_warnings_count=active_warnings_count,
    )


# ─── time_urgency ─────────────────────────────────────────────────────────────

class TestTimeUrgency:
    def test_no_date_contributes_zero(self):
        score, _ = compute()
        assert score == 0.0

    def test_within_7_days(self):
        score, _ = compute(days_ahead=3)
        assert score == 35.0

    def test_exactly_7_days(self):
        score, _ = compute(days_ahead=7)
        assert score == 35.0

    def test_within_15_days(self):
        score, _ = compute(days_ahead=10)
        assert score == 28.0

    def test_exactly_15_days(self):
        score, _ = compute(days_ahead=15)
        assert score == 28.0

    def test_within_30_days(self):
        score, _ = compute(days_ahead=20)
        assert score == 20.0

    def test_exactly_30_days(self):
        score, _ = compute(days_ahead=30)
        assert score == 20.0

    def test_within_60_days(self):
        score, _ = compute(days_ahead=45)
        assert score == 10.0

    def test_exactly_60_days(self):
        score, _ = compute(days_ahead=60)
        assert score == 10.0

    def test_beyond_60_days(self):
        score, _ = compute(days_ahead=90)
        assert score == 4.0

    def test_overdue_within_7_days_bucket(self):
        # data nel passato -> days_ahead < 0 -> fascia <= 7
        score, _ = compute(days_ahead=-5)
        assert score == 35.0


# ─── customer_pressure ───────────────────────────────────────────────────────

class TestCustomerPressure:
    def test_zero_shortage_no_pressure(self):
        score, _ = compute(customer_shortage_qty=0, stock_replenishment_qty=0)
        assert score == 0.0

    def test_small_shortage_base_plus_tier1(self):
        # shortage=50 -> base 20 + tier +5 = 25
        score, _ = compute(customer_shortage_qty=50)
        assert score == 25.0

    def test_shortage_100_tier2(self):
        # shortage=100 -> base 20 + +10 = 30
        score, _ = compute(customer_shortage_qty=100)
        assert score == 30.0

    def test_shortage_500_tier3(self):
        # shortage=500 -> base 20 + +15 = 35
        score, _ = compute(customer_shortage_qty=500)
        assert score == 35.0

    def test_shortage_1000_tier4(self):
        # shortage=1000 -> base 20 + +20 = 40 (cap)
        score, _ = compute(customer_shortage_qty=1000)
        assert score == 40.0

    def test_shortage_above_1000_capped_at_40(self):
        score, _ = compute(customer_shortage_qty=5000)
        assert score == 40.0

    def test_negative_shortage_no_pressure(self):
        score, _ = compute(customer_shortage_qty=-10)
        assert score == 0.0


# ─── stock_pressure ───────────────────────────────────────────────────────────

class TestStockPressure:
    def test_no_replenishment_no_pressure(self):
        score, _ = compute(stock_replenishment_qty=0, target_stock_qty=100)
        assert score == 0.0

    def test_no_target_no_pressure(self):
        score, _ = compute(stock_replenishment_qty=50, target_stock_qty=0)
        assert score == 0.0

    def test_ratio_above_1_no_pressure(self):
        # stock_effective=120, target=100 -> ratio=1.2
        score, _ = compute(stock_replenishment_qty=10, stock_effective_qty=120, target_stock_qty=100)
        assert score == 0.0

    def test_ratio_exactly_1_no_pressure(self):
        score, _ = compute(stock_replenishment_qty=10, stock_effective_qty=100, target_stock_qty=100)
        assert score == 0.0

    def test_ratio_075_to_1(self):
        # stock=80, target=100 -> ratio=0.8
        score, _ = compute(stock_replenishment_qty=20, stock_effective_qty=80, target_stock_qty=100)
        assert score == 4.0

    def test_ratio_050_to_075(self):
        # stock=60, target=100 -> ratio=0.6
        score, _ = compute(stock_replenishment_qty=40, stock_effective_qty=60, target_stock_qty=100)
        assert score == 8.0

    def test_ratio_025_to_050(self):
        # stock=35, target=100 -> ratio=0.35
        score, _ = compute(stock_replenishment_qty=65, stock_effective_qty=35, target_stock_qty=100)
        assert score == 14.0

    def test_ratio_0_to_025(self):
        # stock=10, target=100 -> ratio=0.1
        score, _ = compute(stock_replenishment_qty=90, stock_effective_qty=10, target_stock_qty=100)
        assert score == 20.0

    def test_ratio_negative(self):
        # stock=-20, target=100 -> ratio=-0.2
        score, _ = compute(stock_replenishment_qty=120, stock_effective_qty=-20, target_stock_qty=100)
        assert score == 24.0


# ─── release_penalty ─────────────────────────────────────────────────────────

class TestReleasePenalty:
    def test_launchable_now_no_penalty(self):
        # Base score con shortage piccolo per avere qualcosa da cui sottrarre
        score_free, _ = compute(customer_shortage_qty=50, release_status="launchable_now")
        score_none, _ = compute(customer_shortage_qty=50, release_status=None)
        assert score_free == score_none  # nessuna penalita in entrambi i casi

    def test_launchable_partially_penalty_8(self):
        score_partial, _ = compute(customer_shortage_qty=50, release_status="launchable_partially")
        score_base, _ = compute(customer_shortage_qty=50, release_status=None)
        assert score_base - score_partial == 8.0

    def test_blocked_by_capacity_penalty_18(self):
        score_blocked, _ = compute(customer_shortage_qty=50, release_status="blocked_by_capacity_now")
        score_base, _ = compute(customer_shortage_qty=50, release_status=None)
        assert score_base - score_blocked == 18.0

    def test_penalty_does_not_go_below_zero(self):
        # Senza alcun driver attivo, penalita massima non deve dare score negativo
        score, _ = compute(release_status="blocked_by_capacity_now", active_warnings_count=4)
        assert score == 0.0


# ─── warning_penalty ─────────────────────────────────────────────────────────

class TestWarningPenalty:
    def test_zero_warnings_no_penalty(self):
        score0, _ = compute(customer_shortage_qty=50, active_warnings_count=0)
        score_none, _ = compute(customer_shortage_qty=50)
        assert score0 == score_none

    def test_one_warning_penalty_4(self):
        score1, _ = compute(customer_shortage_qty=50, active_warnings_count=1)
        base, _ = compute(customer_shortage_qty=50)
        assert base - score1 == 4.0

    def test_two_warnings_penalty_8(self):
        score2, _ = compute(customer_shortage_qty=50, active_warnings_count=2)
        base, _ = compute(customer_shortage_qty=50)
        assert base - score2 == 8.0

    def test_three_warnings_penalty_8(self):
        score3, _ = compute(customer_shortage_qty=50, active_warnings_count=3)
        base, _ = compute(customer_shortage_qty=50)
        assert base - score3 == 8.0

    def test_four_or_more_warnings_penalty_12(self):
        score4, _ = compute(customer_shortage_qty=50, active_warnings_count=4)
        base, _ = compute(customer_shortage_qty=50)
        assert base - score4 == 12.0

    def test_many_warnings_penalty_capped_at_12(self):
        score10, _ = compute(customer_shortage_qty=50, active_warnings_count=10)
        score4, _ = compute(customer_shortage_qty=50, active_warnings_count=4)
        assert score10 == score4


# ─── clamp ────────────────────────────────────────────────────────────────────

class TestClamp:
    def test_max_clamp_at_100(self):
        # Massimo teorico: 35+40+24 = 99 -> non supera 100 ma verifichiamo il clamp
        score, _ = compute(
            days_ahead=1,
            customer_shortage_qty=1000,
            stock_replenishment_qty=120,
            stock_effective_qty=-20,
            target_stock_qty=100,
        )
        assert score <= 100.0

    def test_min_clamp_at_zero(self):
        score, _ = compute(
            release_status="blocked_by_capacity_now",
            active_warnings_count=4,
        )
        assert score == 0.0


# ─── priority_band ────────────────────────────────────────────────────────────

class TestPriorityBand:
    def test_band_critical_75_plus(self):
        # 35 (urgency<=7) + 40 (shortage>=1000) = 75 -> critical
        _, band = compute(days_ahead=1, customer_shortage_qty=1000)
        assert band == "critical"

    def test_band_high_50_to_74(self):
        # 35 + 25 (shortage=50) = 60 -> high
        _, band = compute(days_ahead=1, customer_shortage_qty=50)
        assert band == "high"

    def test_band_medium_25_to_49(self):
        # 28 (<=15gg) + 0 = 28 -> medium
        _, band = compute(days_ahead=10)
        assert band == "medium"

    def test_band_low_below_25(self):
        # 4 (>60gg) + 0 = 4 -> low
        _, band = compute(days_ahead=90)
        assert band == "low"

    def test_band_low_zero_score(self):
        _, band = compute()
        assert band == "low"


# ─── guardrail: customer > stock ────────────────────────────────────────────

class TestGuardrail:
    def test_customer_urgency_beats_comparable_stock(self):
        # Customer con shortage 50 (25 pts) + urgenza <=7 (35 pts) = 60
        # Stock puro con ratio negativo (24 pts) + urgenza <=7 (35 pts) = 59 ma customer_shortage=0 qui
        # Verifica che customer driver produce score >= stock puro a parita di urgenza
        customer_score, _ = compute(
            days_ahead=5,
            customer_shortage_qty=50,
        )
        stock_score, _ = compute(
            days_ahead=5,
            stock_replenishment_qty=120,
            stock_effective_qty=-20,
            target_stock_qty=100,
        )
        assert customer_score > stock_score
