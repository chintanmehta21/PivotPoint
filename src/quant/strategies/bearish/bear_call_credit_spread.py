"""Bear Call Credit Spread — >75% POP, defined risk income.

Sells 1x OTM CE and buys 1x further OTM CE on Bank Nifty to create a simple
defined-risk bearish income strategy with high probability of profit.
Score: 75/110
"""
from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from quant.models.contracts import MultiLegPosition, OptionsContract, PositionLeg
from quant.strategies.base_strategy import BaseStrategy
from quant.utils.types import Direction, OptionType, Side, TimeFrame, Underlying

if TYPE_CHECKING:
    from quant.models.contracts import GreeksSnapshot
    from quant.models.market import MarketSnapshot, OptionsChain
    from quant.models.signals import SignalPayload

UNDERLYING = Underlying.BANKNIFTY
LOT_SIZE = 30


class BearCallCreditSpread(BaseStrategy):
    """Bank Nifty Bear Call Credit Spread — >75% POP, defined risk income."""

    name = "Bear Call Credit Spread"
    strategy_id = "BrM2"
    direction = Direction.BEARISH
    timeframe = TimeFrame.MONTHLY
    description = "Bank Nifty Bear Call Credit Spread — >75% POP, defined risk income"

    def evaluate(self, market: MarketSnapshot, chain: OptionsChain) -> SignalPayload | None:
        """Evaluate market conditions for entry signal."""
        if not self.validate_entry(market):
            return None
        # TODO: Implement entry logic — check Bank Nifty resistance, oil-banking transmission
        raise NotImplementedError("Entry evaluation requires live market data")

    def build_position(self, chain: OptionsChain, market: MarketSnapshot) -> MultiLegPosition:
        """Construct the bear call credit spread position.

        Structure:
            Leg 1: Sell 1x OTM CE (collect premium)
            Leg 2: Buy 1x further OTM CE (cap risk)
            Net result: credit entry with defined max loss
        """
        # TODO: Select strikes from chain based on spot price
        raise NotImplementedError("Position building requires live options chain")

    def check_exit(self, position: MultiLegPosition, market: MarketSnapshot) -> SignalPayload | None:
        """Check exit conditions.

        Exit rules:
            - Take profit at 50-65% of max credit received
            - Stop loss at 2x credit received
            - Time-based exit: close 5-7 days before monthly expiry
        """
        # TODO: Implement exit logic
        raise NotImplementedError("Exit checking requires live market data")

    def validate_entry(self, market: MarketSnapshot) -> bool:
        """Validate pre-trade conditions."""
        # TODO: Check Bank Nifty resistance levels, oil prices, market hours, liquidity
        return True
