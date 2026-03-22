"""Async database writer for signal persistence."""
from __future__ import annotations
from decimal import Decimal
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from quant.config.identity import APP_NAME
from quant.config.settings import settings
from quant.outputs.website.schema import Base, SignalRecord, TradeRecord

if TYPE_CHECKING:
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

    async def close(self) -> None:
        """Close the database engine."""
        await self._engine.dispose()
