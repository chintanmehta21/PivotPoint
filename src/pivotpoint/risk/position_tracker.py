"""In-memory position tracking and portfolio Greeks aggregation."""
from __future__ import annotations
from decimal import Decimal
from typing import TYPE_CHECKING

import structlog

from pivotpoint.models.contracts import GreeksSnapshot

if TYPE_CHECKING:
    from pivotpoint.models.signals import SignalPayload

logger = structlog.get_logger()


class PositionTracker:
    """Tracks open positions and calculates portfolio-level metrics."""

    def __init__(self) -> None:
        self._positions: dict[str, SignalPayload] = {}
        self._closed_pnl: Decimal = Decimal("0")

    def add_position(self, signal: SignalPayload) -> None:
        """Add a new position from a signal."""
        self._positions[signal.strategy_id] = signal
        logger.info("Position opened", strategy=signal.strategy_id)

    def close_position(self, strategy_id: str, pnl: Decimal) -> None:
        """Close a position and record P&L."""
        if strategy_id in self._positions:
            del self._positions[strategy_id]
            self._closed_pnl += pnl
            logger.info("Position closed", strategy=strategy_id, pnl=str(pnl))

    @property
    def open_count(self) -> int:
        return len(self._positions)

    @property
    def portfolio_pnl(self) -> Decimal:
        return self._closed_pnl

    @property
    def portfolio_greeks(self) -> GreeksSnapshot:
        """Aggregate Greeks across all open positions."""
        total = GreeksSnapshot()
        for signal in self._positions.values():
            total = GreeksSnapshot(
                delta=total.delta + signal.greeks.delta,
                gamma=total.gamma + signal.greeks.gamma,
                vega=total.vega + signal.greeks.vega,
                theta=total.theta + signal.greeks.theta,
            )
        return total
