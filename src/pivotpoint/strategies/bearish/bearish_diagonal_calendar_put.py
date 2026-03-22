"""Bearish Diagonal/Calendar Put — long vega crisis hedge, triple edge.

Buys 1x monthly PE and sells 1x weekly PE at the same strike to create a
net long vega position with triple edge (Theta + Direction + IV Term Structure).
Score: 82/110
"""
from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from pivotpoint.models.contracts import MultiLegPosition, OptionsContract, PositionLeg
from pivotpoint.strategies.base_strategy import BaseStrategy
from pivotpoint.utils.types import Direction, OptionType, Side, TimeFrame, Underlying

if TYPE_CHECKING:
    from pivotpoint.models.contracts import GreeksSnapshot
    from pivotpoint.models.market import MarketSnapshot, OptionsChain
    from pivotpoint.models.signals import SignalPayload

UNDERLYING = Underlying.NIFTY
LOT_SIZE = 65


class BearishDiagonalCalendarPut(BaseStrategy):
    """Nifty Bearish Diagonal/Calendar Put — long vega crisis hedge, triple edge."""

    name = "Bearish Diagonal Calendar Put"
    strategy_id = "BrW1"
    direction = Direction.BEARISH
    timeframe = TimeFrame.WEEKLY
    description = "Nifty Bearish Diagonal/Calendar Put — long vega crisis hedge, triple edge"

    def evaluate(self, market: MarketSnapshot, chain: OptionsChain) -> SignalPayload | None:
        """Evaluate market conditions for entry signal."""
        if not self.validate_entry(market):
            return None
        # TODO: Implement entry logic — check IV term structure, bearish momentum
        raise NotImplementedError("Entry evaluation requires live market data")

    def build_position(self, chain: OptionsChain, market: MarketSnapshot) -> MultiLegPosition:
        """Construct the diagonal calendar put position.

        Structure:
            Leg 1: Buy 1x monthly PE (long vega, long theta decay edge)
            Leg 2: Sell 1x weekly PE (same strike, short-dated premium collection)
            Phase 2: Roll weekly PE forward each expiry
        """
        # TODO: Select strikes from chain based on spot price
        raise NotImplementedError("Position building requires live options chain")

    def check_exit(self, position: MultiLegPosition, market: MarketSnapshot) -> SignalPayload | None:
        """Check exit conditions.

        Exit rules:
            - Take profit when IV crush on short leg exceeds long leg decay
            - Stop loss if term structure inverts unfavorably
            - Roll short leg on weekly expiry Thursday
        """
        # TODO: Implement exit logic
        raise NotImplementedError("Exit checking requires live market data")

    def validate_entry(self, market: MarketSnapshot) -> bool:
        """Validate pre-trade conditions."""
        # TODO: Check IV term structure (contango preferred), market hours, liquidity
        return True
