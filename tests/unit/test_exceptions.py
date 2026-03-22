"""Tests for custom exceptions."""
from datetime import date
from decimal import Decimal

import pytest

from quant.utils.exceptions import (
    PivotPointError, ContractExpiredError, MissingGreeksError,
    IlliquidStrikeError, MarketClosedError, SignalValidationError,
)


def test_base_exception():
    with pytest.raises(PivotPointError):
        raise PivotPointError("test")


def test_contract_expired_carries_context():
    err = ContractExpiredError("NIFTY23100CE", date(2026, 1, 1))
    assert err.symbol == "NIFTY23100CE"
    assert err.expiry == date(2026, 1, 1)
    assert "expired" in str(err).lower()


def test_missing_greeks_carries_context():
    err = MissingGreeksError("NIFTY23100CE")
    assert err.symbol == "NIFTY23100CE"


def test_illiquid_strike_carries_context():
    err = IlliquidStrikeError("NIFTY23100CE", Decimal("23100"))
    assert err.strike == Decimal("23100")


def test_market_closed_default():
    err = MarketClosedError()
    assert err.market == "NSE"


def test_signal_validation_carries_context():
    err = SignalValidationError("BW1", "VIX too low")
    assert err.strategy_id == "BW1"
    assert "VIX" in err.reason
