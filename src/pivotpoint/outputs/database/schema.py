"""SQLAlchemy ORM models for signal and trade persistence."""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, Float, Integer, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase

from pivotpoint.config.identity import APP_NAME_SNAKE


class Base(DeclarativeBase):
    pass


class SignalRecord(Base):
    """Persisted trading signal."""
    __tablename__ = f"{APP_NAME_SNAKE}_signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.now)
    strategy_id = Column(String(20), nullable=False, index=True)
    strategy_name = Column(String(100), nullable=False)
    underlying = Column(String(20), nullable=False)
    direction = Column(String(10), nullable=False)
    timeframe = Column(String(15), nullable=False)
    signal_type = Column(String(15), nullable=False)
    max_profit = Column(Numeric(12, 2), nullable=False)
    max_loss = Column(Numeric(12, 2), nullable=False)
    risk_reward_ratio = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)
    greeks_json = Column(Text, default="{}")
    position_json = Column(Text, default="[]")
    notes = Column(Text, default="")


class TradeRecord(Base):
    """Trade execution record linked to a signal."""
    __tablename__ = f"{APP_NAME_SNAKE}_trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    signal_id = Column(Integer, nullable=False, index=True)
    execution_time = Column(DateTime, default=datetime.now)
    fill_price = Column(Numeric(12, 2))
    status = Column(String(20), default="OPEN")  # OPEN, CLOSED, EXPIRED
    actual_pnl = Column(Numeric(12, 2))


class StrategyPerformance(Base):
    """Aggregated strategy performance metrics."""
    __tablename__ = f"{APP_NAME_SNAKE}_strategy_performance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(String(20), unique=True, nullable=False)
    total_trades = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    avg_rr = Column(Float, default=0.0)
    total_pnl = Column(Numeric(12, 2), default=0)
