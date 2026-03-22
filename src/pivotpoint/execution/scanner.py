"""Strategy scanner — evaluates all strategies against current market data."""
from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import structlog

from pivotpoint.config.identity import APP_NAME
from pivotpoint.strategies.registry import StrategyRegistry

if TYPE_CHECKING:
    from pivotpoint.models.market import MarketSnapshot, OptionsChain
    from pivotpoint.models.signals import SignalPayload
    from pivotpoint.risk.risk_manager import RiskManager

logger = structlog.get_logger()


@dataclass
class ScanResult:
    """Results from a strategy scan with partial failure tracking."""
    signals: list[SignalPayload] = field(default_factory=list)
    errors: dict[str, str] = field(default_factory=dict)  # strategy_id -> error message

    @property
    def success_count(self) -> int:
        return len(self.signals)

    @property
    def failure_count(self) -> int:
        return len(self.errors)


class StrategyScanner:
    """Scans all registered strategies and collects signals."""

    def __init__(self, registry: StrategyRegistry | None = None, risk_manager: RiskManager | None = None) -> None:
        self._registry = registry or StrategyRegistry()
        self._risk_manager = risk_manager

    async def scan(self, market: MarketSnapshot, chain: OptionsChain) -> ScanResult:
        """Evaluate all strategies against current market data.

        Strategies run sync via asyncio.to_thread to avoid blocking.
        """
        result = ScanResult()
        strategies = self._registry.all()

        logger.info("Scan started", app=APP_NAME, strategy_count=len(strategies))

        for strategy_id, strategy in strategies.items():
            try:
                signal = await asyncio.to_thread(strategy.evaluate, market, chain)
                if signal is not None:
                    if self._risk_manager and not self._risk_manager.pre_trade_check(signal):
                        logger.warning("Signal rejected by risk manager", strategy=strategy_id)
                        continue
                    result.signals.append(signal)
            except NotImplementedError:
                pass  # Expected for unimplemented strategies
            except Exception as e:
                result.errors[strategy_id] = str(e)
                logger.error("Strategy evaluation failed", strategy=strategy_id, error=str(e))

        logger.info(
            "Scan completed",
            signals=result.success_count,
            errors=result.failure_count,
        )
        return result
