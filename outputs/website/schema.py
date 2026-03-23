"""SQLAlchemy ORM models for signal and trade persistence."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase

from quant.config.identity import APP_NAME_SNAKE


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


class DailyReportRecord(Base):
    """Persisted daily report for website/ML pipeline."""
    __tablename__ = f"{APP_NAME_SNAKE}_daily_reports"
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_date = Column(String(10), nullable=False, index=True)
    report_type = Column(String(10), nullable=False)
    report_status = Column(String(20), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    holiday_name = Column(String(100))
    next_trading_day = Column(String(10))
    market_macros_json = Column(Text, default="{}")
    strategy_results_json = Column(Text, default="[]")
    portfolios_json = Column(Text, default="[]")
    error_category = Column(String(50))
    error_detail = Column(Text)


class VirtualPortfolioRecord(Base):
    __tablename__ = f"{APP_NAME_SNAKE}_virtual_portfolios"
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_date = Column(String(10), nullable=False, index=True)
    tier = Column(String(20), nullable=False)
    threshold = Column(Integer, nullable=False)
    active_positions = Column(Integer, default=0)
    total_trades = Column(Integer, default=0)
    realized_pnl = Column(Numeric(12, 2), default=0)
    unrealized_pnl = Column(Numeric(12, 2), default=0)
    total_pnl = Column(Numeric(12, 2), default=0)
    win_rate = Column(Float, default=0.0)
    best_strategy = Column(String(20))
    worst_strategy = Column(String(20))


class VirtualTradeDBRecord(Base):
    __tablename__ = f"{APP_NAME_SNAKE}_virtual_trades"
    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_id = Column(String(36), nullable=False, unique=True)
    tier = Column(String(20), nullable=False)
    strategy_id = Column(String(20), nullable=False, index=True)
    direction = Column(String(10), nullable=False)
    entry_date = Column(String(10), nullable=False)
    entry_price = Column(Numeric(12, 2), nullable=False)
    exit_date = Column(String(10))
    exit_price = Column(Numeric(12, 2))
    status = Column(String(10), default="OPEN")
    realized_pnl = Column(Numeric(12, 2))
