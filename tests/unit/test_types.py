"""Tests for enums and type aliases."""
from pivotpoint.utils.types import OptionType, Direction, TimeFrame, Side, Underlying


def test_option_type_values():
    assert OptionType.CE.value == "CE"
    assert OptionType.PE.value == "PE"


def test_direction_values():
    assert Direction.BULLISH.value == "BULLISH"
    assert Direction.BEARISH.value == "BEARISH"


def test_timeframe_values():
    assert set(t.value for t in TimeFrame) == {"WEEKLY", "MONTHLY", "QUARTERLY"}


def test_underlying_values():
    assert Underlying.NIFTY.value == "NIFTY"
    assert Underlying.BANKNIFTY.value == "BANKNIFTY"
