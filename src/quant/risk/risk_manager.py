"""Pre-trade and portfolio risk management."""
from __future__ import annotations
from typing import TYPE_CHECKING

import structlog

from quant.config.settings import settings

if TYPE_CHECKING:
    from quant.models.signals import SignalPayload

logger = structlog.get_logger()


class RiskManager:
    """Validates signals against portfolio risk limits."""

    def __init__(self) -> None:
        self._risk = settings.risk

    def pre_trade_check(self, signal: SignalPayload) -> bool:
        """Run all pre-trade risk checks. Returns True if signal passes."""
        checks = [
            self._check_max_loss(signal),
            self._check_vix_regime(signal),
        ]
        return all(checks)

    def _check_max_loss(self, signal: SignalPayload) -> bool:
        """Check if signal's max loss exceeds portfolio limit."""
        if signal.max_loss > self._risk.max_portfolio_loss:
            logger.warning(
                "Signal exceeds max portfolio loss",
                strategy=signal.strategy_id,
                max_loss=str(signal.max_loss),
                limit=str(self._risk.max_portfolio_loss),
            )
            return False
        return True

    def _check_vix_regime(self, signal: SignalPayload) -> bool:
        """Check VIX regime alignment (placeholder — needs live VIX data)."""
        # TODO: Implement VIX regime check with live data
        return True
