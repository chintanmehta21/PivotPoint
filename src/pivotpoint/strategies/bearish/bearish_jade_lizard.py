"""Bearish Jade Lizard — ZERO upside risk, profits even on rally.

Sells 1x OTM PE and 1x OTM CE while buying 1x further OTM CE wing to eliminate
upside risk entirely. Only bearish strategy with zero upside risk.
Score: 80/110
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


class BearishJadeLizard(BaseStrategy):
    """Nifty Bearish Jade Lizard — ZERO upside risk, profits even on rally."""

    name = "Bearish Jade Lizard"
    strategy_id = "BrM1"
    direction = Direction.BEARISH
    timeframe = TimeFrame.MONTHLY
    description = "Nifty Bearish Jade Lizard — ZERO upside risk, profits even on rally"

    def evaluate(self, market: MarketSnapshot, chain: OptionsChain) -> SignalPayload | None:
        """Evaluate market conditions for entry signal."""
        if not self.validate_entry(market):
            return None
        # TODO: Implement entry logic — check premium levels, bearish bias
        raise NotImplementedError("Entry evaluation requires live market data")

    def build_position(self, chain: OptionsChain, market: MarketSnapshot) -> MultiLegPosition:
        """Construct the bearish jade lizard position.

        Structure:
            Leg 1: Sell 1x OTM PE (naked put — requires stop at defined level)
            Leg 2: Sell 1x OTM CE (collect premium)
            Leg 3: Buy 1x further OTM CE (wing — caps upside risk to ZERO)
            Net result: credit entry with zero upside risk
        """
        # TODO: Select strikes from chain based on spot price
        raise NotImplementedError("Position building requires live options chain")

    def check_exit(self, position: MultiLegPosition, market: MarketSnapshot) -> SignalPayload | None:
        """Check exit conditions.

        Exit rules:
            - Take profit at target premium decay
            - Stop loss on naked put if spot breaks below defined support
            - Time-based exit before monthly expiry
        """
        # TODO: Implement exit logic
        raise NotImplementedError("Exit checking requires live market data")

    def validate_entry(self, market: MarketSnapshot) -> bool:
        """Validate pre-trade conditions."""
        # TODO: Check premium levels, support/resistance, market hours, liquidity
        return True
