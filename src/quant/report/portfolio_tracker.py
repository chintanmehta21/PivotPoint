"""Three-tier virtual portfolio simulation."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import structlog

from quant.models.daily_report import (
    TIER_THRESHOLDS,
    PortfolioTier,
    VirtualPortfolio,
    VirtualTradeRecord,
)
from quant.utils.types import Direction

logger = structlog.get_logger()


class PortfolioTracker:
    def __init__(self) -> None:
        self._trades: dict[PortfolioTier, list[VirtualTradeRecord]] = {tier: [] for tier in PortfolioTier}

    def process_entry(
        self,
        strategy_id: str,
        direction: Direction,
        confidence_score: float,
        entry_price: Decimal,
        entry_date: date,
    ) -> None:
        for tier, threshold in TIER_THRESHOLDS.items():
            if confidence_score >= threshold:
                trade = VirtualTradeRecord(
                    trade_id=str(uuid4()),
                    tier=tier,
                    strategy_id=strategy_id,
                    direction=direction,
                    entry_date=entry_date,
                    entry_price=entry_price,
                )
                self._trades[tier].append(trade)
                logger.debug("virtual_trade_opened", tier=tier, strategy_id=strategy_id)

    def process_exit(
        self,
        strategy_id: str,
        exit_price: Decimal,
        exit_date: date,
    ) -> None:
        for tier in PortfolioTier:
            for trade in reversed(self._trades[tier]):
                if trade.strategy_id == strategy_id and trade.status == "OPEN":
                    trade.exit_price = exit_price
                    trade.exit_date = exit_date
                    trade.status = "CLOSED"
                    if trade.direction == Direction.BEARISH:
                        trade.realized_pnl = trade.entry_price - exit_price
                    else:
                        trade.realized_pnl = exit_price - trade.entry_price
                    logger.debug(
                        "virtual_trade_closed",
                        tier=tier,
                        strategy_id=strategy_id,
                        realized_pnl=trade.realized_pnl,
                    )
                    break

    def get_snapshots(self) -> list[VirtualPortfolio]:
        snapshots = []
        for tier in PortfolioTier:
            trades = self._trades[tier]
            open_trades = [t for t in trades if t.status == "OPEN"]
            closed_trades = [t for t in trades if t.status == "CLOSED"]
            realized = sum((t.realized_pnl or Decimal("0")) for t in closed_trades)
            unrealized = Decimal("0")  # TODO: mark-to-market
            wins = sum(1 for t in closed_trades if (t.realized_pnl or Decimal("0")) > 0)
            win_rate = wins / len(closed_trades) if closed_trades else 0.0
            best = (
                max(closed_trades, key=lambda t: t.realized_pnl or Decimal("0")).strategy_id if closed_trades else "—"
            )
            worst = (
                min(closed_trades, key=lambda t: t.realized_pnl or Decimal("0")).strategy_id if closed_trades else "—"
            )
            snapshots.append(
                VirtualPortfolio(
                    tier=tier,
                    threshold=TIER_THRESHOLDS[tier],
                    active_positions=len(open_trades),
                    total_trades=len(trades),
                    realized_pnl=realized,
                    unrealized_pnl=unrealized,
                    total_pnl=realized + unrealized,
                    win_rate=win_rate,
                    best_strategy=best,
                    worst_strategy=worst,
                )
            )
        return snapshots
