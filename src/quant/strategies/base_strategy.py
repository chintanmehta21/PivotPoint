"""Abstract base class for all options trading strategies."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

import structlog

from quant.config.identity import APP_NAME
from quant.models.contracts import GreeksSnapshot, MultiLegPosition
from quant.models.signals import SignalPayload
from quant.utils.types import Direction, SignalType, TimeFrame, Underlying

if TYPE_CHECKING:
    from quant.models.market import MarketSnapshot, OptionsChain

logger = structlog.get_logger()


class BaseStrategy(ABC):
    """Abstract base class all trading strategies inherit from.

    Subclasses must define class-level attributes:
        name, strategy_id, direction, timeframe, description
    And implement abstract methods:
        evaluate, build_position, check_exit, validate_entry
    """

    name: str
    strategy_id: str
    direction: Direction
    timeframe: TimeFrame
    description: str

    @abstractmethod
    def evaluate(self, market: MarketSnapshot, chain: OptionsChain) -> SignalPayload | None:
        """Evaluate market conditions and generate an entry signal if criteria met."""
        ...

    @abstractmethod
    def build_position(self, chain: OptionsChain, market: MarketSnapshot) -> MultiLegPosition:
        """Construct the multi-leg position for this strategy."""
        ...

    @abstractmethod
    def check_exit(self, position: MultiLegPosition, market: MarketSnapshot) -> SignalPayload | None:
        """Check if an exit or adjustment signal should be generated."""
        ...

    @abstractmethod
    def validate_entry(self, market: MarketSnapshot) -> bool:
        """Validate pre-trade conditions (VIX regime, liquidity, market hours)."""
        ...

    def calculate_position_greeks(self, position: MultiLegPosition) -> GreeksSnapshot:
        """Aggregate Greeks across all legs of a position."""
        total_delta = 0.0
        total_gamma = 0.0
        total_vega = 0.0
        total_theta = 0.0
        # TODO: Requires live Greeks data from MarketDataProvider
        return GreeksSnapshot(delta=total_delta, gamma=total_gamma, vega=total_vega, theta=total_theta)

    def _create_signal(
        self,
        position: MultiLegPosition,
        market: MarketSnapshot,
        signal_type: SignalType,
        confidence: float = 0.0,
        notes: str = "",
    ) -> SignalPayload:
        """Create a SignalPayload from current position and market state."""
        greeks = self.calculate_position_greeks(position)
        max_profit = Decimal("0")  # TODO: Calculate from position structure
        max_loss = Decimal("0")  # TODO: Calculate from position structure
        rr_ratio = float(max_profit / max_loss) if max_loss != 0 else 0.0

        return SignalPayload(
            timestamp=datetime.now(),
            strategy_name=self.name,
            strategy_id=self.strategy_id,
            underlying=market.underlying,
            timeframe=self.timeframe,
            direction=self.direction,
            position=position,
            max_profit=max_profit,
            max_loss=max_loss,
            risk_reward_ratio=rr_ratio,
            confidence_score=confidence,
            greeks=greeks,
            signal_type=signal_type,
            notes=notes,
        )

    def __repr__(self) -> str:
        return f"<{APP_NAME} Strategy: {self.name} ({self.direction.value}/{self.timeframe.value})>"
