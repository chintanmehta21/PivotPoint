"""Tests for risk manager."""
from decimal import Decimal
from quant.risk.risk_manager import RiskManager


def test_signal_within_limits_passes(sample_signal):
    rm = RiskManager()
    assert rm.pre_trade_check(sample_signal) is True


def test_signal_exceeding_max_loss_fails(sample_signal):
    # Modify signal to exceed limit
    sample_signal.max_loss = Decimal("999999999")
    rm = RiskManager()
    assert rm.pre_trade_check(sample_signal) is False
