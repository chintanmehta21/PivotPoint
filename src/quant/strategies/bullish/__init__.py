"""Bullish options strategies."""
from quant.strategies.bullish.call_ratio_backspread import CallRatioBackspread
from quant.strategies.bullish.supertrend_bull_call_spread import SupertrendBullCallSpread
from quant.strategies.bullish.modified_butterfly import ModifiedButterfly
from quant.strategies.bullish.bullish_diagonal_calendar import BullishDiagonalCalendar
from quant.strategies.bullish.bullish_adjusted_iron_fly import BullishAdjustedIronFly
from quant.strategies.bullish.broken_wing_call_butterfly import BrokenWingCallButterfly

__all__ = [
    "CallRatioBackspread",
    "SupertrendBullCallSpread",
    "ModifiedButterfly",
    "BullishDiagonalCalendar",
    "BullishAdjustedIronFly",
    "BrokenWingCallButterfly",
]
