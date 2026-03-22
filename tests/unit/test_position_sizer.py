"""Tests for position sizing."""
from decimal import Decimal
from pivotpoint.execution.position_sizer import PositionSizer


def test_basic_sizing():
    sizer = PositionSizer(risk_per_trade_pct=2.0)
    lots = sizer.calculate_lots(Decimal("500000"), Decimal("5000"))
    assert lots >= 1


def test_minimum_one_lot():
    sizer = PositionSizer(risk_per_trade_pct=0.01)
    lots = sizer.calculate_lots(Decimal("10000"), Decimal("50000"))
    assert lots == 1


def test_zero_max_loss():
    sizer = PositionSizer()
    lots = sizer.calculate_lots(Decimal("500000"), Decimal("0"))
    assert lots == 1
