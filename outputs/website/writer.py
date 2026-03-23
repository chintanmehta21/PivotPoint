"""Async database writer for signal persistence."""
from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

import structlog
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from outputs.website.schema import Base, SignalRecord, TradeRecord
from quant.config.identity import APP_NAME
from quant.config.settings import settings

if TYPE_CHECKING:
    from outputs.website.daily_report import DailyReport
    from quant.models.signals import SignalPayload

logger = structlog.get_logger()


class DatabaseWriter:
    """Writes signals and trades to the database asynchronously."""

    def __init__(self, db_url: str | None = None) -> None:
        url = db_url or settings.database.url
        self._engine = create_async_engine(url, echo=False)
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False)

    async def initialize(self) -> None:
        """Create all tables if they don't exist."""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized", app=APP_NAME)

    async def write_signal(self, signal: SignalPayload) -> int:
        """Write a signal to the database and return its ID."""
        record = SignalRecord(
            timestamp=signal.timestamp,
            strategy_id=signal.strategy_id,
            strategy_name=signal.strategy_name,
            underlying=signal.underlying.value,
            direction=signal.direction.value,
            timeframe=signal.timeframe.value,
            signal_type=signal.signal_type.value,
            max_profit=signal.max_profit,
            max_loss=signal.max_loss,
            risk_reward_ratio=signal.risk_reward_ratio,
            confidence_score=signal.confidence_score,
            greeks_json=signal.greeks.model_dump_json(),
            position_json=signal.position.model_dump_json(),
            notes=signal.notes,
        )
        async with self._session_factory() as session:
            session.add(record)
            await session.commit()
            await session.refresh(record)
            logger.info("Signal persisted", signal_id=record.id, strategy=signal.strategy_id)
            return record.id

    async def update_trade(self, signal_id: int, status: str, pnl: Decimal) -> None:
        """Update or create a trade record."""
        async with self._session_factory() as session:
            record = TradeRecord(signal_id=signal_id, status=status, actual_pnl=pnl)
            session.add(record)
            await session.commit()

    async def write_daily_report(self, report: DailyReport) -> int:
        from outputs.website.schema import DailyReportRecord, VirtualPortfolioRecord
        record = DailyReportRecord(
            report_date=report.date.isoformat(),
            report_type=report.report_type.value,
            report_status=report.report_status.value,
            timestamp=report.timestamp,
            holiday_name=report.holiday_name,
            next_trading_day=report.next_trading_day.isoformat() if report.next_trading_day else None,
            market_macros_json=report.market_macros.model_dump_json() if report.market_macros else "{}",
            strategy_results_json="[]",
            portfolios_json="[]",
            error_category=report.error_category.value if report.error_category else None,
            error_detail=report.error_detail,
        )
        async with self._session_factory() as session:
            session.add(record)
            for p in report.portfolios:
                pr = VirtualPortfolioRecord(
                    report_date=report.date.isoformat(),
                    tier=p.tier.value,
                    threshold=p.threshold,
                    active_positions=p.active_positions,
                    total_trades=p.total_trades,
                    realized_pnl=p.realized_pnl,
                    unrealized_pnl=p.unrealized_pnl,
                    total_pnl=p.total_pnl,
                    win_rate=p.win_rate,
                    best_strategy=p.best_strategy,
                    worst_strategy=p.worst_strategy,
                )
                session.add(pr)
            await session.commit()
            await session.refresh(record)
            logger.info("Daily report persisted", report_id=record.id, status=report.report_status.value)
            return record.id

    async def close(self) -> None:
        """Close the database engine."""
        await self._engine.dispose()
