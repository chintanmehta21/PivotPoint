"""Daily report data models."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field

from quant.models.signals import SignalPayload
from quant.utils.types import Direction, TimeFrame


class ReportType(StrEnum):
    MORNING = "MORNING"
    EVENING = "EVENING"


class ReportStatus(StrEnum):
    SUCCESS = "SUCCESS"
    MARKET_HOLIDAY = "MARKET_HOLIDAY"
    ERROR = "ERROR"


class ErrorCategory(StrEnum):
    MARKET_DATA_UNAVAILABLE = "MARKET_DATA_UNAVAILABLE"
    STRATEGY_EVALUATION_FAILED = "STRATEGY_EVALUATION_FAILED"
    HOLIDAY_CHECK_FAILED = "HOLIDAY_CHECK_FAILED"
    API_RATE_LIMITED = "API_RATE_LIMITED"
    AUTHENTICATION_EXPIRED = "AUTHENTICATION_EXPIRED"
    DISPATCH_FAILED = "DISPATCH_FAILED"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


ERROR_LABELS: dict[ErrorCategory, str] = {
    ErrorCategory.MARKET_DATA_UNAVAILABLE: "Market Data Unavailable",
    ErrorCategory.STRATEGY_EVALUATION_FAILED: "Strategy Evaluation Failed",
    ErrorCategory.HOLIDAY_CHECK_FAILED: "Holiday Check Failed",
    ErrorCategory.API_RATE_LIMITED: "API Rate Limited",
    ErrorCategory.AUTHENTICATION_EXPIRED: "Authentication Expired",
    ErrorCategory.DISPATCH_FAILED: "Report Dispatch Failed",
    ErrorCategory.UNKNOWN_ERROR: "Unexpected Error",
}


class PortfolioTier(StrEnum):
    CONSERVATIVE = "CONSERVATIVE"
    MODERATE = "MODERATE"
    AGGRESSIVE = "AGGRESSIVE"


TIER_THRESHOLDS: dict[PortfolioTier, int] = {
    PortfolioTier.CONSERVATIVE: 85,
    PortfolioTier.MODERATE: 75,
    PortfolioTier.AGGRESSIVE: 0,
}


class MarketMacros(BaseModel):
    """Full market snapshot. Formatter displays only the required subset."""

    # --- DISPLAYED in main report (required) ---
    nifty_price: Decimal
    nifty_change_pct: float
    banknifty_price: Decimal
    banknifty_change_pct: float
    india_vix: float
    vix_change: float
    nifty_pcr_oi: float
    nifty_max_pain: Decimal
    banknifty_max_pain: Decimal
    nifty_iv_percentile: float
    banknifty_iv_percentile: float
    fii_net_cash: Decimal
    dii_net_cash: Decimal

    # --- STORED for ML feature store / drill-down (optional) ---
    advance_decline_ratio: float | None = None
    pct_above_20dma: float | None = None
    pct_above_50dma: float | None = None
    pct_above_200dma: float | None = None

    nifty_atm_iv: float | None = None
    banknifty_atm_iv: float | None = None
    nifty_25delta_skew: float | None = None
    iv_term_structure_spread: float | None = None
    volatility_risk_premium: float | None = None
    nifty_pcr_volume: float | None = None
    total_call_oi: int | None = None
    total_put_oi: int | None = None
    oi_change_calls: int | None = None
    oi_change_puts: int | None = None
    net_premium_flow: Decimal | None = None

    net_gamma_exposure: Decimal | None = None
    call_wall: Decimal | None = None
    put_wall: Decimal | None = None
    gamma_flip_level: Decimal | None = None
    vanna_exposure: float | None = None
    charm_exposure: float | None = None

    fii_net_derivatives: Decimal | None = None
    dii_net_derivatives: Decimal | None = None
    fii_index_futures_long_short_ratio: float | None = None

    nifty_support_levels: list[Decimal] = Field(default_factory=list)
    nifty_resistance_levels: list[Decimal] = Field(default_factory=list)
    supertrend_signal: str | None = None
    nifty_rsi: float | None = None
    nifty_macd_state: str | None = None

    realized_vol_5d: float | None = None
    realized_vol_10d: float | None = None
    realized_vol_20d: float | None = None
    realized_vol_60d: float | None = None
    iv_rv_spread: float | None = None
    pcr_momentum: float | None = None
    skew_slope_velocity: float | None = None
    gamma_flip_proximity: float | None = None


class StrategyResult(BaseModel):
    """Result of evaluating a single strategy."""

    strategy_id: str
    strategy_name: str
    direction: Direction
    timeframe: TimeFrame
    signal: SignalPayload | None = None
    confidence_score: float | None = None
    error: str | None = None


class VirtualPortfolio(BaseModel):
    """Snapshot of a virtual portfolio tier."""

    tier: PortfolioTier
    threshold: int
    active_positions: int
    total_trades: int
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    total_pnl: Decimal
    win_rate: float
    best_strategy: str
    worst_strategy: str


class VirtualTradeRecord(BaseModel):
    """Individual virtual trade for DB persistence."""

    trade_id: str
    tier: PortfolioTier
    strategy_id: str
    direction: Direction
    entry_date: date
    entry_price: Decimal
    exit_date: date | None = None
    exit_price: Decimal | None = None
    status: str = "OPEN"
    realized_pnl: Decimal | None = None
    signal_payload: SignalPayload | None = None


class DailyReport(BaseModel):
    """Root model for a daily report."""

    report_type: ReportType
    report_status: ReportStatus
    date: date
    timestamp: datetime
    holiday_name: str | None = None
    next_trading_day: date | None = None
    market_macros: MarketMacros | None = None
    strategy_results: list[StrategyResult] = Field(default_factory=list)
    top_3_bullish: list[StrategyResult] = Field(default_factory=list)
    top_3_bearish: list[StrategyResult] = Field(default_factory=list)
    portfolios: list[VirtualPortfolio] = Field(default_factory=list)
    error_category: ErrorCategory | None = None
    error_detail: str | None = None
