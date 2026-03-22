"""Bullish-Adjusted Iron Fly — 2-phase, highest theta in pipeline.

Phase 1 enters a neutral iron fly (sell ATM CE+PE, buy wings) to maximize theta
collection. Phase 2 rolls the short put closer on bullish confirmation, converting
the position to a bullish-biased structure with the highest theta yield in the system.
Score: 90/110
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


class BullishAdjustedIronFly(BaseStrategy):
    """Nifty Bullish-Adjusted Iron Fly — 2-phase, highest theta in pipeline."""

    name = "Bullish Adjusted Iron Fly"
    strategy_id = "BQ1"
    direction = Direction.BULLISH
    timeframe = TimeFrame.QUARTERLY
    description = "Nifty Bullish-Adjusted Iron Fly — 2-phase, highest theta in pipeline"

    def evaluate(self, market: MarketSnapshot, chain: OptionsChain) -> SignalPayload | None:
        """Evaluate market conditions for entry signal."""
        if not self.validate_entry(market):
            return None
        # TODO: Implement entry logic — Phase 1 enters on neutral conditions,
        # Phase 2 triggers on bullish confirmation (spot breaks above resistance)
        raise NotImplementedError("Entry evaluation requires live market data")

    def build_position(self, chain: OptionsChain, market: MarketSnapshot) -> MultiLegPosition:
        """Construct the iron fly position.

        Structure (Phase 1 — neutral entry):
            Leg 1: Sell 1x ATM CE (collect premium)
            Leg 2: Sell 1x ATM PE (collect premium)
            Leg 3: Buy 1x OTM CE wing (protection)
            Leg 4: Buy 1x OTM PE wing (protection)

        Phase 2 (bullish adjustment — triggered by check_exit):
            Roll short PE from ATM to closer strike (e.g., ATM-100)
            This shifts delta positive while maintaining theta advantage
        """
        # TODO: Select strikes from chain based on spot price
        # atm_strike = round_to_strike(market.spot_price)
        # ce_wing = atm_strike + 500
        # pe_wing = atm_strike - 500
        raise NotImplementedError("Position building requires live options chain")

    def check_exit(self, position: MultiLegPosition, market: MarketSnapshot) -> SignalPayload | None:
        """Check exit, adjustment, and phase transition conditions.

        Exit rules:
            - Phase 1 -> Phase 2: Roll short PE on bullish confirmation
            - Take profit at 50% of max premium collected
            - Stop loss if breaching either wing strike
            - Time-based: begin unwinding 2 weeks before quarterly expiry
        """
        # TODO: Implement exit and phase transition logic
        raise NotImplementedError("Exit checking requires live market data")

    def validate_entry(self, market: MarketSnapshot) -> bool:
        """Validate pre-trade conditions."""
        # TODO: Check VIX regime (12-18 ideal for iron fly), market hours, liquidity
        return True
