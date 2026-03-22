"""Bear Put Condor — Adaptive Bear, absolute loss cap both sides.

Buys 1x upper PE, sells 1x PE, sells 1x PE, and buys 1x lower PE in a 4-leg condor
creating the SAFEST bearish strategy with max loss equal to debit in ALL scenarios.
Score: 87/110
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


class BearPutCondor(BaseStrategy):
    """Nifty Bear Put Condor — Adaptive Bear, absolute loss cap both sides."""

    name = "Bear Put Condor"
    strategy_id = "BrQ2"
    direction = Direction.BEARISH
    timeframe = TimeFrame.QUARTERLY
    description = "Nifty Bear Put Condor — Adaptive Bear, absolute loss cap both sides"

    def evaluate(self, market: MarketSnapshot, chain: OptionsChain) -> SignalPayload | None:
        """Evaluate market conditions for entry signal."""
        if not self.validate_entry(market):
            return None
        # TODO: Implement entry logic — check quarterly bearish thesis, IV levels
        raise NotImplementedError("Entry evaluation requires live market data")

    def build_position(self, chain: OptionsChain, market: MarketSnapshot) -> MultiLegPosition:
        """Construct the bear put condor position.

        Structure:
            Leg 1: Buy 1x upper PE (highest strike)
            Leg 2: Sell 1x PE (upper-middle strike)
            Leg 3: Sell 1x PE (lower-middle strike)
            Leg 4: Buy 1x lower PE (lowest strike — caps downside loss)
            Net result: debit entry, max loss = debit in ALL scenarios both directions
            Dynamic rolling capability for adaptation.
        """
        # TODO: Select strikes from chain based on spot price
        raise NotImplementedError("Position building requires live options chain")

    def check_exit(self, position: MultiLegPosition, market: MarketSnapshot) -> SignalPayload | None:
        """Check exit conditions.

        Exit rules:
            - Take profit when spot enters body of condor
            - Max loss is capped (debit paid) — no stop loss needed
            - Dynamic roll if market conditions change
            - Time-based management for quarterly expiry
        """
        # TODO: Implement exit logic
        raise NotImplementedError("Exit checking requires live market data")

    def validate_entry(self, market: MarketSnapshot) -> bool:
        """Validate pre-trade conditions."""
        # TODO: Check quarterly setup, IV levels, market hours, liquidity
        return True
