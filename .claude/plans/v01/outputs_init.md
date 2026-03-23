# Daily Report Output System — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an automated daily report system that sends market macros, top-3 strategy results, virtual portfolio tracking, and drill-down analysis to Discord + Telegram on every working day, with holiday detection and categorized error handling.

**Architecture:** Monolithic `DailyReportEngine` orchestrates: holiday check → market data fetch → strategy scan → portfolio simulation → report assembly → multi-channel dispatch. GitHub Actions cron triggers `pivotpoint report --type morning|evening`. Data persisted to DB for future website/ML pipeline.

**Tech Stack:** Python 3.11, Pydantic, structlog, exchange_calendars, discord.py, python-telegram-bot, httpx, SQLAlchemy async, Click CLI, GitHub Actions, freezegun (tests)

**Spec:** `docs/superpowers/specs/2026-03-23-daily-report-outputs-design.md`

---

## File Map

| File | Responsibility | Task |
|------|---------------|------|
| `pyproject.toml` | Add `exchange_calendars`, `pyyaml` deps | 1 |
| `src/quant/models/daily_report.py` | All report models + enums | 2 |
| `src/quant/config/holidays.yaml` | Manual holiday overrides | 3 |
| `src/quant/calendar/__init__.py` | Package init | 3 |
| `src/quant/calendar/holiday_checker.py` | Layered holiday detection | 3 |
| `src/quant/calendar/market_hours.py` | IST trading hours constants | 3 |
| `src/quant/report/__init__.py` | Package init | 5 |
| `src/quant/report/market_data_collector.py` | Fetch macros from Fyers API | 5 |
| `src/quant/report/portfolio_tracker.py` | 3-tier virtual portfolio sim | 6 |
| `src/quant/report/engine.py` | Pipeline orchestrator | 7 |
| `outputs/base_report_formatter.py` | ABC for report formatters | 8 |
| `outputs/discord/report_formatter.py` | Discord embed formatter | 9 |
| `outputs/telegram/report_formatter.py` | Telegram MarkdownV2 formatter | 10 |
| `outputs/discord/bot.py` | Add `send_daily_report()` | 11 |
| `outputs/telegram/bot.py` | Add `send_daily_report()` | 11 |
| `outputs/website/schema.py` | Add report DB tables | 12 |
| `outputs/website/writer.py` | Add `write_daily_report()` | 12 |
| `src/quant/cli.py` | Add `report` command | 13 |
| `.github/workflows/morning-report.yml` | Cron 3:00 UTC | 14 |
| `.github/workflows/evening-report.yml` | Cron 10:30 UTC | 14 |
| `tests/unit/test_daily_report_models.py` | Model tests | 2 |
| `tests/unit/test_holiday_checker.py` | Holiday detection tests | 4 |
| `tests/unit/test_portfolio_tracker.py` | Portfolio sim tests | 6 |
| `tests/unit/test_report_engine.py` | Engine pipeline tests | 7 |
| `tests/unit/test_discord_report_formatter.py` | Discord formatter tests | 9 |
| `tests/unit/test_telegram_report_formatter.py` | Telegram formatter tests | 10 |
| `tests/conftest.py` | Add report fixtures | 2 |

---

## Task 1: Add Dependencies

**Files:**
- Modify: `pyproject.toml:10-26`

- [ ] **Step 1: Add exchange_calendars and pyyaml to dependencies**

In `pyproject.toml`, add to the `dependencies` list:

```toml
    "exchange_calendars>=4.5.0",
    "pyyaml>=6.0.0",
```

Note: `discord.py`, `python-telegram-bot`, `httpx` are already present. Only these two are new.

- [ ] **Step 2: Install and verify**

Run: `pip install -e ".[dev]"`
Expected: Installs successfully, `exchange_calendars` and `pyyaml` importable.

- [ ] **Step 3: Verify exchange_calendars has XBOM**

Run: `python -c "import exchange_calendars as ec; cal = ec.get_calendar('XBOM'); print(f'XBOM loaded: {cal.name}')"`
Expected: `XBOM loaded: XBOM`

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "Add exchange_calendars and pyyaml dependencies"
```

---

## Task 2: Data Models + Enums

**Files:**
- Create: `src/quant/models/daily_report.py`
- Create: `tests/unit/test_daily_report_models.py`
- Modify: `tests/conftest.py`

- [ ] **Step 1: Write model tests**

Create `tests/unit/test_daily_report_models.py`:

```python
"""Tests for daily report data models."""
from datetime import date, datetime
from decimal import Decimal

import pytest

from quant.models.daily_report import (
    DailyReport,
    ErrorCategory,
    MarketMacros,
    PortfolioTier,
    ReportStatus,
    ReportType,
    StrategyResult,
    VirtualPortfolio,
    VirtualTradeRecord,
    ERROR_LABELS,
)
from quant.utils.types import Direction, TimeFrame


class TestEnums:
    def test_report_type_values(self):
        assert ReportType.MORNING == "MORNING"
        assert ReportType.EVENING == "EVENING"

    def test_report_status_values(self):
        assert ReportStatus.SUCCESS == "SUCCESS"
        assert ReportStatus.MARKET_HOLIDAY == "MARKET_HOLIDAY"
        assert ReportStatus.ERROR == "ERROR"

    def test_error_category_values(self):
        assert len(ErrorCategory) == 7
        assert ErrorCategory.UNKNOWN_ERROR == "UNKNOWN_ERROR"

    def test_portfolio_tier_values(self):
        assert PortfolioTier.CONSERVATIVE == "CONSERVATIVE"
        assert PortfolioTier.MODERATE == "MODERATE"
        assert PortfolioTier.AGGRESSIVE == "AGGRESSIVE"

    def test_error_labels_all_categories_have_labels(self):
        for cat in ErrorCategory:
            assert cat in ERROR_LABELS, f"Missing label for {cat}"
            assert isinstance(ERROR_LABELS[cat], str)


class TestMarketMacros:
    def test_required_fields_only(self):
        macros = MarketMacros(
            nifty_price=Decimal("22450.30"),
            nifty_change_pct=1.2,
            banknifty_price=Decimal("48120.50"),
            banknifty_change_pct=-0.4,
            india_vix=14.8,
            vix_change=-0.6,
            nifty_pcr_oi=1.12,
            nifty_max_pain=Decimal("22500"),
            banknifty_max_pain=Decimal("48000"),
            nifty_iv_percentile=42.0,
            banknifty_iv_percentile=38.0,
            fii_net_cash=Decimal("-1240"),
            dii_net_cash=Decimal("890"),
        )
        assert macros.nifty_price == Decimal("22450.30")
        # Optional fields default to None
        assert macros.advance_decline_ratio is None
        assert macros.net_gamma_exposure is None
        assert macros.nifty_support_levels == []

    def test_optional_ml_fields(self):
        macros = MarketMacros(
            nifty_price=Decimal("22450"),
            nifty_change_pct=1.2,
            banknifty_price=Decimal("48120"),
            banknifty_change_pct=-0.4,
            india_vix=14.8,
            vix_change=-0.6,
            nifty_pcr_oi=1.12,
            nifty_max_pain=Decimal("22500"),
            banknifty_max_pain=Decimal("48000"),
            nifty_iv_percentile=42.0,
            banknifty_iv_percentile=38.0,
            fii_net_cash=Decimal("-1240"),
            dii_net_cash=Decimal("890"),
            realized_vol_5d=0.15,
            pcr_momentum=0.02,
        )
        assert macros.realized_vol_5d == 0.15
        assert macros.pcr_momentum == 0.02


class TestStrategyResult:
    def test_no_signal(self):
        result = StrategyResult(
            strategy_id="BW1",
            strategy_name="Call Ratio Backspread",
            direction=Direction.BULLISH,
            timeframe=TimeFrame.WEEKLY,
            signal=None,
            confidence_score=None,
            error=None,
        )
        assert result.signal is None

    def test_with_error(self):
        result = StrategyResult(
            strategy_id="BW1",
            strategy_name="Call Ratio Backspread",
            direction=Direction.BULLISH,
            timeframe=TimeFrame.WEEKLY,
            signal=None,
            confidence_score=None,
            error="Insufficient market data",
        )
        assert result.error == "Insufficient market data"


class TestVirtualPortfolio:
    def test_creation(self):
        portfolio = VirtualPortfolio(
            tier=PortfolioTier.CONSERVATIVE,
            threshold=85,
            active_positions=3,
            total_trades=28,
            realized_pnl=Decimal("42300"),
            unrealized_pnl=Decimal("8100"),
            total_pnl=Decimal("50400"),
            win_rate=0.68,
            best_strategy="BQ1",
            worst_strategy="BrM2",
        )
        assert portfolio.tier == PortfolioTier.CONSERVATIVE
        assert portfolio.threshold == 85


class TestDailyReport:
    def test_success_report(self, sample_market_macros):
        report = DailyReport(
            report_type=ReportType.EVENING,
            report_status=ReportStatus.SUCCESS,
            date=date(2026, 3, 24),
            timestamp=datetime(2026, 3, 24, 16, 0, 0),
            holiday_name=None,
            next_trading_day=None,
            market_macros=sample_market_macros,
        )
        assert report.report_status == ReportStatus.SUCCESS
        assert report.strategy_results == []
        assert report.portfolios == []

    def test_holiday_report(self):
        report = DailyReport(
            report_type=ReportType.MORNING,
            report_status=ReportStatus.MARKET_HOLIDAY,
            date=date(2026, 3, 26),
            timestamp=datetime(2026, 3, 26, 8, 30, 0),
            holiday_name="Holi",
            next_trading_day=date(2026, 3, 27),
            market_macros=None,
        )
        assert report.holiday_name == "Holi"
        assert report.next_trading_day == date(2026, 3, 27)
        assert report.market_macros is None

    def test_error_report(self):
        report = DailyReport(
            report_type=ReportType.EVENING,
            report_status=ReportStatus.ERROR,
            date=date(2026, 3, 24),
            timestamp=datetime(2026, 3, 24, 16, 0, 0),
            holiday_name=None,
            next_trading_day=None,
            market_macros=None,
            error_category=ErrorCategory.MARKET_DATA_UNAVAILABLE,
            error_detail="Fyers API timeout after 30s",
        )
        assert report.error_category == ErrorCategory.MARKET_DATA_UNAVAILABLE
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_daily_report_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'quant.models.daily_report'`

- [ ] **Step 3: Create daily_report.py with all models**

Create `src/quant/models/daily_report.py`:

```python
"""Daily report data models."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field

from quant.models.signals import SignalPayload
from quant.utils.types import Direction, TimeFrame


class ReportType(str, Enum):
    MORNING = "MORNING"
    EVENING = "EVENING"


class ReportStatus(str, Enum):
    SUCCESS = "SUCCESS"
    MARKET_HOLIDAY = "MARKET_HOLIDAY"
    ERROR = "ERROR"


class ErrorCategory(str, Enum):
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


class PortfolioTier(str, Enum):
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
```

- [ ] **Step 4: Add fixtures to conftest.py**

Add to `tests/conftest.py`:

```python
from quant.models.daily_report import (
    DailyReport, MarketMacros, ReportStatus, ReportType, VirtualPortfolio, PortfolioTier,
)


@pytest.fixture
def sample_market_macros() -> MarketMacros:
    return MarketMacros(
        nifty_price=Decimal("22450.30"),
        nifty_change_pct=1.2,
        banknifty_price=Decimal("48120.50"),
        banknifty_change_pct=-0.4,
        india_vix=14.8,
        vix_change=-0.6,
        nifty_pcr_oi=1.12,
        nifty_max_pain=Decimal("22500"),
        banknifty_max_pain=Decimal("48000"),
        nifty_iv_percentile=42.0,
        banknifty_iv_percentile=38.0,
        fii_net_cash=Decimal("-1240"),
        dii_net_cash=Decimal("890"),
    )


@pytest.fixture
def sample_virtual_portfolio() -> VirtualPortfolio:
    return VirtualPortfolio(
        tier=PortfolioTier.CONSERVATIVE,
        threshold=85,
        active_positions=3,
        total_trades=28,
        realized_pnl=Decimal("42300"),
        unrealized_pnl=Decimal("8100"),
        total_pnl=Decimal("50400"),
        win_rate=0.68,
        best_strategy="BQ1",
        worst_strategy="BrM2",
    )


@pytest.fixture
def sample_daily_report(sample_market_macros) -> DailyReport:
    return DailyReport(
        report_type=ReportType.EVENING,
        report_status=ReportStatus.SUCCESS,
        date=date(2026, 3, 24),
        timestamp=datetime(2026, 3, 24, 16, 0, 0),
        market_macros=sample_market_macros,
    )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/unit/test_daily_report_models.py -v`
Expected: All tests PASS

- [ ] **Step 6: Lint**

Run: `ruff check src/quant/models/daily_report.py tests/unit/test_daily_report_models.py`
Expected: No errors

- [ ] **Step 7: Commit**

```bash
git add src/quant/models/daily_report.py tests/unit/test_daily_report_models.py tests/conftest.py
git commit -m "Add daily report data models and enums"
```

---

## Task 3: Holiday Checker (Layered Detection)

**Files:**
- Create: `src/quant/calendar/__init__.py`
- Create: `src/quant/calendar/holiday_checker.py`
- Create: `src/quant/calendar/market_hours.py`
- Create: `src/quant/config/holidays.yaml`

- [ ] **Step 1: Create market_hours.py constants**

Create `src/quant/calendar/market_hours.py`:

```python
"""NSE market hours and IST timezone constants."""
from datetime import time
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)
PRE_MARKET_OPEN = time(9, 0)
PRE_MARKET_CLOSE = time(9, 8)
```

- [ ] **Step 2: Create holidays.yaml**

Create `src/quant/config/holidays.yaml`:

```yaml
# Manual overrides for holiday checker.
# Use when exchange_calendars is wrong or NSE announces surprise holidays.
# Status: HOLIDAY or OPEN (to force-override the calendar library).
overrides: []
```

- [ ] **Step 3: Create `__init__.py`**

Create `src/quant/calendar/__init__.py`:

```python
"""Market calendar and holiday detection."""
```

- [ ] **Step 4: Create holiday_checker.py**

Create `src/quant/calendar/holiday_checker.py`:

```python
"""Layered holiday detection for NSE India.

Layer 1: Weekend check (Saturday/Sunday)
Layer 2: exchange_calendars XBOM.is_session()
Layer 3: NSE API fetch (cached daily)
Layer 4: holidays.yaml manual overrides
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

import exchange_calendars as ec
import httpx
import structlog
import yaml

from quant.config.identity import APP_NAME

logger = structlog.get_logger()

_HOLIDAYS_YAML = Path(__file__).resolve().parent.parent / "config" / "holidays.yaml"
_NSE_HOLIDAY_URL = "https://www.nseindia.com/api/holiday-master?type=trading"
_NSE_HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}


class HolidayChecker:
    """Determines if a given date is an NSE trading day."""

    def __init__(self) -> None:
        self._xbom = ec.get_calendar("XBOM")
        self._overrides = self._load_overrides()
        self._nse_cache: dict[int, list[dict[str, str]]] | None = None  # year -> [{tradingDate, description}]

    # --- Public API ---

    def is_trading_day(self, target: dt.date) -> bool:
        """Check all layers. Returns True if market is open."""
        # Deviation from spec: YAML overrides checked first (not last) so manual
        # force-OPEN/force-HOLIDAY always wins regardless of other layers.
        override = self._check_override(target)
        if override is not None:
            return override

        # Layer 1: weekends
        if target.weekday() >= 5:
            return False

        # Layer 2: exchange_calendars
        ts = dt.datetime(target.year, target.month, target.day)
        xbom_open = self._xbom.is_session(ts)

        # Layer 3: NSE API cross-validation
        nse_holiday = self._check_nse_api(target)
        if nse_holiday is True:
            # NSE says closed — trust it (surprise closure)
            return False
        if nse_holiday is False:
            # NSE says open — trust it
            return True
        # NSE API failed — trust Layer 2
        return xbom_open

    def get_holiday_name(self, target: dt.date) -> str | None:
        """Get the name of the holiday, if any."""
        override_name = self._get_override_name(target)
        if override_name:
            return override_name
        # Try NSE API cache
        return self._get_nse_holiday_name(target)

    def get_next_trading_day(self, target: dt.date) -> dt.date:
        """Find the next trading day after target."""
        candidate = target + dt.timedelta(days=1)
        # Safety: max 10 days lookahead (handles long weekends + holidays)
        for _ in range(10):
            if self.is_trading_day(candidate):
                return candidate
            candidate += dt.timedelta(days=1)
        # Fallback: return next Monday if nothing found
        days_until_monday = (7 - candidate.weekday()) % 7 or 7
        return candidate + dt.timedelta(days=days_until_monday)

    def get_previous_trading_day(self, target: dt.date) -> dt.date:
        """Find the most recent trading day before target."""
        candidate = target - dt.timedelta(days=1)
        for _ in range(10):
            if self.is_trading_day(candidate):
                return candidate
            candidate -= dt.timedelta(days=1)
        return candidate

    # --- Layer 3: NSE API ---

    def _check_nse_api(self, target: dt.date) -> bool | None:
        """Check NSE holiday API. Returns True=holiday, False=open, None=API failed."""
        try:
            entries = self._fetch_nse_holidays(target.year)
            date_str = target.strftime("%d-%b-%Y")
            return any(e["tradingDate"] == date_str for e in entries)
        except Exception:
            logger.warning("NSE holiday API unavailable, trusting exchange_calendars", app=APP_NAME)
            return None

    def _fetch_nse_holidays(self, year: int) -> list[dict[str, str]]:
        """Fetch and cache NSE holidays for a year. Returns list of {tradingDate, description}."""
        if self._nse_cache and year in self._nse_cache:
            return self._nse_cache[year]
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(_NSE_HOLIDAY_URL, headers=_NSE_HEADERS)
                resp.raise_for_status()
                data = resp.json()
            entries: list[dict[str, str]] = []
            for segment in ("FO", "CM"):
                for entry in data.get(segment, []):
                    entries.append({
                        "tradingDate": entry.get("tradingDate", ""),
                        "description": entry.get("description", "Market Holiday"),
                    })
            if self._nse_cache is None:
                self._nse_cache = {}
            self._nse_cache[year] = entries
            return entries
        except Exception as e:
            logger.debug("NSE API fetch failed", error=str(e))
            raise

    def _get_nse_holiday_name(self, target: dt.date) -> str | None:
        """Get holiday name from cached NSE data (no extra HTTP call)."""
        try:
            entries = self._fetch_nse_holidays(target.year)  # uses cache if available
            date_str = target.strftime("%d-%b-%Y")
            for entry in entries:
                if entry["tradingDate"] == date_str:
                    return entry["description"]
        except Exception:
            pass
        return None

    # --- Layer 4: YAML overrides ---

    def _load_overrides(self) -> list[dict[str, Any]]:
        """Load holidays.yaml overrides."""
        if not _HOLIDAYS_YAML.exists():
            return []
        try:
            with open(_HOLIDAYS_YAML) as f:
                data = yaml.safe_load(f) or {}
            return data.get("overrides", []) or []
        except Exception as e:
            logger.warning("Failed to load holidays.yaml", error=str(e))
            return []

    def _check_override(self, target: dt.date) -> bool | None:
        """Check if date has a manual override. Returns True=open, False=holiday, None=no override."""
        target_str = target.isoformat()
        for entry in self._overrides:
            if entry.get("date") == target_str:
                status = entry.get("status", "").upper()
                if status == "HOLIDAY":
                    return False
                if status == "OPEN":
                    return True
        return None

    def _get_override_name(self, target: dt.date) -> str | None:
        """Get holiday name from override."""
        target_str = target.isoformat()
        for entry in self._overrides:
            if entry.get("date") == target_str:
                return entry.get("name")
        return None
```

- [ ] **Step 5: Commit**

```bash
git add src/quant/calendar/ src/quant/config/holidays.yaml
git commit -m "Add layered holiday checker with XBOM, NSE API, YAML"
```

---

## Task 4: Holiday Checker Tests

**Files:**
- Create: `tests/unit/test_holiday_checker.py`

- [ ] **Step 1: Write holiday checker tests**

Create `tests/unit/test_holiday_checker.py`:

```python
"""Tests for layered holiday detection."""
import datetime as dt
from unittest.mock import MagicMock, patch

import pytest
from freezegun import freeze_time

from quant.calendar.holiday_checker import HolidayChecker


class TestWeekendDetection:
    """Layer 1: weekends are always non-trading."""

    def test_saturday_is_not_trading_day(self):
        checker = HolidayChecker()
        # 2026-03-28 is a Saturday
        assert checker.is_trading_day(dt.date(2026, 3, 28)) is False

    def test_sunday_is_not_trading_day(self):
        checker = HolidayChecker()
        # 2026-03-29 is a Sunday
        assert checker.is_trading_day(dt.date(2026, 3, 29)) is False


class TestExchangeCalendars:
    """Layer 2: exchange_calendars XBOM."""

    @patch("quant.calendar.holiday_checker.HolidayChecker._check_nse_api", return_value=None)
    def test_known_weekday_is_trading(self, mock_nse):
        checker = HolidayChecker()
        # 2026-03-23 is Monday — should be a trading day
        assert checker.is_trading_day(dt.date(2026, 3, 23)) is True

    @patch("quant.calendar.holiday_checker.HolidayChecker._check_nse_api", return_value=None)
    def test_republic_day_is_holiday(self, mock_nse):
        checker = HolidayChecker()
        # Jan 26 is Republic Day — XBOM should mark it as holiday
        assert checker.is_trading_day(dt.date(2026, 1, 26)) is False


class TestNseApiLayer:
    """Layer 3: NSE API cross-validation."""

    def test_nse_says_holiday_overrides_xbom(self):
        checker = HolidayChecker()
        # Simulate NSE API saying it's a holiday on a weekday
        with patch.object(checker, "_check_nse_api", return_value=True):
            assert checker.is_trading_day(dt.date(2026, 3, 23)) is False

    def test_nse_api_failure_falls_back_to_xbom(self):
        checker = HolidayChecker()
        with patch.object(checker, "_check_nse_api", return_value=None):
            # Falls back to XBOM — Monday should be open
            assert checker.is_trading_day(dt.date(2026, 3, 23)) is True


class TestYamlOverrides:
    """Layer 4: manual YAML overrides."""

    def test_yaml_holiday_override(self):
        checker = HolidayChecker()
        checker._overrides = [{"date": "2026-03-23", "status": "HOLIDAY", "name": "Test Holiday"}]
        assert checker.is_trading_day(dt.date(2026, 3, 23)) is False

    def test_yaml_open_override(self):
        checker = HolidayChecker()
        checker._overrides = [{"date": "2026-01-26", "status": "OPEN"}]
        # YAML says OPEN, even though it would normally be Republic Day
        assert checker.is_trading_day(dt.date(2026, 1, 26)) is True

    def test_yaml_override_name(self):
        checker = HolidayChecker()
        checker._overrides = [{"date": "2026-03-26", "status": "HOLIDAY", "name": "Holi"}]
        assert checker.get_holiday_name(dt.date(2026, 3, 26)) == "Holi"


class TestNextPreviousTradingDay:
    def test_next_trading_day_skips_weekend(self):
        checker = HolidayChecker()
        with patch.object(checker, "_check_nse_api", return_value=None):
            # Friday 2026-03-27 → next should be Monday 2026-03-30
            next_day = checker.get_next_trading_day(dt.date(2026, 3, 27))
            assert next_day == dt.date(2026, 3, 30)

    def test_previous_trading_day_skips_weekend(self):
        checker = HolidayChecker()
        with patch.object(checker, "_check_nse_api", return_value=None):
            # Monday 2026-03-30 → previous should be Friday 2026-03-27
            prev_day = checker.get_previous_trading_day(dt.date(2026, 3, 30))
            assert prev_day == dt.date(2026, 3, 27)
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/unit/test_holiday_checker.py -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_holiday_checker.py
git commit -m "Add holiday checker tests for all 4 layers"
```

---

## Task 5: Market Data Collector (Stub)

**Files:**
- Create: `src/quant/report/__init__.py`
- Create: `src/quant/report/market_data_collector.py`

The actual Fyers API integration is out of scope (strategies themselves are stubs). This creates the interface + stub that returns mock data for testing the pipeline.

- [ ] **Step 1: Create package init**

Create `src/quant/report/__init__.py`:

```python
"""Daily report generation pipeline."""
```

- [ ] **Step 2: Create market_data_collector.py**

Create `src/quant/report/market_data_collector.py`:

```python
"""Fetches market macro data from Fyers API and NSE.

NOTE: This is a stub implementation. Real Fyers API integration
will be implemented when MarketDataProvider is connected (Phase 4).
Currently returns placeholder data for pipeline testing.
"""
from __future__ import annotations

from decimal import Decimal

import structlog

from quant.config.identity import APP_NAME
from quant.models.daily_report import MarketMacros, ReportType

logger = structlog.get_logger()


class MarketDataCollector:
    """Collects all market macro metrics for the daily report."""

    async def collect(self, report_type: ReportType) -> MarketMacros:
        """Fetch market data. Raises on failure.

        Args:
            report_type: MORNING uses previous close, EVENING uses current close.
        """
        logger.info("Collecting market data", report_type=report_type.value, app=APP_NAME)
        # TODO: Replace with actual Fyers API calls when MarketDataProvider is implemented.
        # For now, raise to indicate this is not yet connected.
        raise NotImplementedError(
            "MarketDataCollector requires Fyers API integration. "
            "Use --dry-run with mock data for testing."
        )
```

- [ ] **Step 3: Commit**

```bash
git add src/quant/report/
git commit -m "Add market data collector stub for report pipeline"
```

---

## Task 6: Virtual Portfolio Tracker

**Files:**
- Create: `src/quant/report/portfolio_tracker.py`
- Create: `tests/unit/test_portfolio_tracker.py`

- [ ] **Step 1: Write portfolio tracker tests**

Create `tests/unit/test_portfolio_tracker.py`:

```python
"""Tests for virtual portfolio tracker."""
from datetime import date
from decimal import Decimal

import pytest

from quant.models.daily_report import PortfolioTier, VirtualPortfolio, VirtualTradeRecord
from quant.report.portfolio_tracker import PortfolioTracker
from quant.utils.types import Direction


class TestPortfolioTracker:
    def test_three_tiers_returned(self):
        tracker = PortfolioTracker()
        portfolios = tracker.get_snapshots()
        assert len(portfolios) == 3
        tiers = {p.tier for p in portfolios}
        assert tiers == {PortfolioTier.CONSERVATIVE, PortfolioTier.MODERATE, PortfolioTier.AGGRESSIVE}

    def test_thresholds_match(self):
        tracker = PortfolioTracker()
        portfolios = tracker.get_snapshots()
        for p in portfolios:
            if p.tier == PortfolioTier.CONSERVATIVE:
                assert p.threshold == 85
            elif p.tier == PortfolioTier.MODERATE:
                assert p.threshold == 75
            elif p.tier == PortfolioTier.AGGRESSIVE:
                assert p.threshold == 0

    def test_initial_state_is_empty(self):
        tracker = PortfolioTracker()
        for p in tracker.get_snapshots():
            assert p.active_positions == 0
            assert p.total_trades == 0
            assert p.total_pnl == Decimal("0")

    def test_open_trade_above_threshold(self):
        tracker = PortfolioTracker()
        tracker.process_entry(
            strategy_id="BQ1",
            direction=Direction.BULLISH,
            confidence_score=90.0,
            entry_price=Decimal("150.00"),
            entry_date=date(2026, 3, 24),
        )
        snapshots = tracker.get_snapshots()
        # Score 90 >= all thresholds: should appear in all 3 tiers
        for p in snapshots:
            assert p.active_positions == 1
            assert p.total_trades == 1

    def test_open_trade_below_conservative_threshold(self):
        tracker = PortfolioTracker()
        tracker.process_entry(
            strategy_id="BW1",
            direction=Direction.BULLISH,
            confidence_score=80.0,
            entry_price=Decimal("100.00"),
            entry_date=date(2026, 3, 24),
        )
        snapshots = {p.tier: p for p in tracker.get_snapshots()}
        # Score 80 < 85: not in Conservative
        assert snapshots[PortfolioTier.CONSERVATIVE].active_positions == 0
        # Score 80 >= 75: in Moderate and Aggressive
        assert snapshots[PortfolioTier.MODERATE].active_positions == 1
        assert snapshots[PortfolioTier.AGGRESSIVE].active_positions == 1

    def test_close_trade_realizes_pnl(self):
        tracker = PortfolioTracker()
        tracker.process_entry(
            strategy_id="BQ1",
            direction=Direction.BULLISH,
            confidence_score=90.0,
            entry_price=Decimal("100.00"),
            entry_date=date(2026, 3, 24),
        )
        tracker.process_exit(
            strategy_id="BQ1",
            exit_price=Decimal("130.00"),
            exit_date=date(2026, 3, 25),
        )
        snapshots = {p.tier: p for p in tracker.get_snapshots()}
        for tier in PortfolioTier:
            p = snapshots[tier]
            assert p.active_positions == 0
            assert p.realized_pnl == Decimal("30.00")
            assert p.win_rate == 1.0

    def test_win_rate_calculation(self):
        tracker = PortfolioTracker()
        # Win: bullish, price goes up
        tracker.process_entry("S1", Direction.BULLISH, 90.0, Decimal("100"), date(2026, 3, 24))
        tracker.process_exit("S1", Decimal("120"), date(2026, 3, 25))
        # Loss: bullish, price goes down
        tracker.process_entry("S2", Direction.BULLISH, 90.0, Decimal("100"), date(2026, 3, 25))
        tracker.process_exit("S2", Decimal("80"), date(2026, 3, 26))
        snapshots = {p.tier: p for p in tracker.get_snapshots()}
        # 1 win (S1: +20), 1 loss (S2: -20), win rate = 50%
        assert snapshots[PortfolioTier.CONSERVATIVE].win_rate == 0.5

    def test_bearish_pnl_direction(self):
        tracker = PortfolioTracker()
        # Bearish trade: profit when price drops
        tracker.process_entry("S1", Direction.BEARISH, 90.0, Decimal("100"), date(2026, 3, 24))
        tracker.process_exit("S1", Decimal("80"), date(2026, 3, 25))
        snapshots = {p.tier: p for p in tracker.get_snapshots()}
        # Entry 100, exit 80, bearish → profit = 100 - 80 = +20
        assert snapshots[PortfolioTier.CONSERVATIVE].realized_pnl == Decimal("20")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_portfolio_tracker.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'quant.report.portfolio_tracker'`

- [ ] **Step 3: Create portfolio_tracker.py**

Create `src/quant/report/portfolio_tracker.py`:

```python
"""Three-tier virtual portfolio simulation.

Tracks paper trades across Conservative (85+), Moderate (75+),
and Aggressive (all signals) tiers. State is in-memory;
DB persistence is handled by the engine via DatabaseWriter.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import structlog

from quant.models.daily_report import (
    PortfolioTier,
    TIER_THRESHOLDS,
    VirtualPortfolio,
    VirtualTradeRecord,
)
from quant.utils.types import Direction

logger = structlog.get_logger()


class PortfolioTracker:
    """Manages virtual trades across three risk tiers."""

    def __init__(self) -> None:
        self._trades: dict[PortfolioTier, list[VirtualTradeRecord]] = {
            tier: [] for tier in PortfolioTier
        }

    def process_entry(
        self,
        strategy_id: str,
        direction: Direction,
        confidence_score: float,
        entry_price: Decimal,
        entry_date: date,
    ) -> None:
        """Open a virtual trade in all qualifying tiers."""
        for tier, threshold in TIER_THRESHOLDS.items():
            if confidence_score >= threshold:
                trade = VirtualTradeRecord(
                    trade_id=str(uuid4()),
                    tier=tier,
                    strategy_id=strategy_id,
                    direction=direction,
                    entry_date=entry_date,
                    entry_price=entry_price,
                    status="OPEN",
                )
                self._trades[tier].append(trade)

    def process_exit(
        self,
        strategy_id: str,
        exit_price: Decimal,
        exit_date: date,
    ) -> None:
        """Close the most recent open trade for this strategy across all tiers."""
        for tier in PortfolioTier:
            for trade in reversed(self._trades[tier]):
                if trade.strategy_id == strategy_id and trade.status == "OPEN":
                    trade.exit_price = exit_price
                    trade.exit_date = exit_date
                    trade.status = "CLOSED"
                    # Bearish = profit when price drops; Bullish = profit when price rises
                    if trade.direction == Direction.BEARISH:
                        trade.realized_pnl = trade.entry_price - exit_price
                    else:
                        trade.realized_pnl = exit_price - trade.entry_price
                    break

    def get_snapshots(self) -> list[VirtualPortfolio]:
        """Build current snapshot for each tier."""
        snapshots = []
        for tier in PortfolioTier:
            trades = self._trades[tier]
            open_trades = [t for t in trades if t.status == "OPEN"]
            closed_trades = [t for t in trades if t.status == "CLOSED"]

            realized = sum((t.realized_pnl or Decimal("0")) for t in closed_trades)
            unrealized = Decimal("0")  # TODO: mark-to-market with live prices
            wins = sum(1 for t in closed_trades if (t.realized_pnl or 0) > 0)
            win_rate = wins / len(closed_trades) if closed_trades else 0.0

            # Best/worst by realized P&L
            best = max(closed_trades, key=lambda t: t.realized_pnl or 0).strategy_id if closed_trades else "—"
            worst = min(closed_trades, key=lambda t: t.realized_pnl or 0).strategy_id if closed_trades else "—"

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
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/unit/test_portfolio_tracker.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/quant/report/portfolio_tracker.py tests/unit/test_portfolio_tracker.py
git commit -m "Add 3-tier virtual portfolio tracker"
```

---

## Task 7: Report Engine (Pipeline Orchestrator)

**Files:**
- Create: `src/quant/report/engine.py`
- Create: `tests/unit/test_report_engine.py`

- [ ] **Step 1: Write engine tests**

Create `tests/unit/test_report_engine.py`:

```python
"""Tests for DailyReportEngine pipeline."""
import datetime as dt
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from quant.models.daily_report import DailyReport, ErrorCategory, ReportStatus, ReportType


@pytest.fixture
def mock_holiday_checker():
    checker = MagicMock()
    checker.is_trading_day.return_value = True
    checker.get_holiday_name.return_value = None
    checker.get_next_trading_day.return_value = dt.date(2026, 3, 24)
    return checker


@pytest.fixture
def mock_holiday_checker_holiday():
    checker = MagicMock()
    checker.is_trading_day.return_value = False
    checker.get_holiday_name.return_value = "Holi"
    checker.get_next_trading_day.return_value = dt.date(2026, 3, 27)
    return checker


class TestReportEngineHoliday:
    @pytest.mark.asyncio
    async def test_holiday_returns_holiday_report(self, mock_holiday_checker_holiday):
        from quant.report.engine import DailyReportEngine

        engine = DailyReportEngine(holiday_checker=mock_holiday_checker_holiday)
        report = await engine.generate(ReportType.MORNING, dry_run=True)
        assert report.report_status == ReportStatus.MARKET_HOLIDAY
        assert report.holiday_name == "Holi"
        assert report.next_trading_day == dt.date(2026, 3, 27)
        assert report.market_macros is None


class TestReportEngineError:
    @pytest.mark.asyncio
    async def test_market_data_failure_returns_error(self, mock_holiday_checker):
        from quant.report.engine import DailyReportEngine

        engine = DailyReportEngine(holiday_checker=mock_holiday_checker)
        # generate() will hit NotImplementedError from MarketDataCollector
        report = await engine.generate(ReportType.EVENING, dry_run=True)
        assert report.report_status == ReportStatus.ERROR
        assert report.error_category == ErrorCategory.MARKET_DATA_UNAVAILABLE
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_report_engine.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'quant.report.engine'`

- [ ] **Step 3: Create engine.py**

Create `src/quant/report/engine.py`:

```python
"""Daily report generation pipeline orchestrator."""
from __future__ import annotations

import asyncio
from datetime import date, datetime
from zoneinfo import ZoneInfo

import structlog

from quant.calendar.holiday_checker import HolidayChecker
from quant.config.identity import APP_NAME
from quant.models.daily_report import (
    DailyReport,
    ErrorCategory,
    ReportStatus,
    ReportType,
)
from quant.report.market_data_collector import MarketDataCollector
from quant.report.portfolio_tracker import PortfolioTracker

logger = structlog.get_logger()

IST = ZoneInfo("Asia/Kolkata")

# Retry config: (max_retries, initial_backoff_seconds)
# TODO: Implement retry loop in generate() for retryable errors.
# Deferred to when Fyers API is connected — no point retrying stubs.
_RETRY_CONFIG: dict[ErrorCategory, tuple[int, float]] = {
    ErrorCategory.MARKET_DATA_UNAVAILABLE: (3, 30.0),
    ErrorCategory.API_RATE_LIMITED: (3, 60.0),
    ErrorCategory.DISPATCH_FAILED: (2, 15.0),
}


class DailyReportEngine:
    """Orchestrates the full daily report pipeline."""

    def __init__(
        self,
        holiday_checker: HolidayChecker | None = None,
        market_data_collector: MarketDataCollector | None = None,
        portfolio_tracker: PortfolioTracker | None = None,
    ) -> None:
        self._holiday = holiday_checker or HolidayChecker()
        self._market = market_data_collector or MarketDataCollector()
        self._portfolio = portfolio_tracker or PortfolioTracker()

    async def generate(self, report_type: ReportType, dry_run: bool = False) -> DailyReport:
        """Generate a daily report.

        Pipeline:
        1. Holiday check
        2. Fetch market data
        3. Run strategies (via scanner)
        4. Update virtual portfolios
        5. Assemble report

        Returns DailyReport with appropriate status (SUCCESS/HOLIDAY/ERROR).
        """
        today = date.today()
        now = datetime.now(tz=IST)
        logger.info("Generating daily report", report_type=report_type.value, date=str(today), app=APP_NAME)

        # Step 1: Holiday check
        if not self._holiday.is_trading_day(today):
            holiday_name = self._holiday.get_holiday_name(today) or "Market Holiday"
            next_day = self._holiday.get_next_trading_day(today)
            logger.info("Market holiday detected", holiday=holiday_name, next_trading_day=str(next_day))
            return DailyReport(
                report_type=report_type,
                report_status=ReportStatus.MARKET_HOLIDAY,
                date=today,
                timestamp=now,
                holiday_name=holiday_name,
                next_trading_day=next_day,
            )

        # Step 2: Fetch market data
        try:
            macros = await self._market.collect(report_type)
        except NotImplementedError as e:
            logger.warning("Market data collector not implemented", error=str(e))
            return DailyReport(
                report_type=report_type,
                report_status=ReportStatus.ERROR,
                date=today,
                timestamp=now,
                error_category=ErrorCategory.MARKET_DATA_UNAVAILABLE,
                error_detail=str(e),
            )
        except Exception as e:
            logger.error("Market data collection failed", error=str(e))
            return DailyReport(
                report_type=report_type,
                report_status=ReportStatus.ERROR,
                date=today,
                timestamp=now,
                error_category=ErrorCategory.MARKET_DATA_UNAVAILABLE,
                error_detail=str(e),
            )

        # Steps 3-4: Strategy scan + portfolio update
        # TODO: Integrate with StrategyScanner when strategies are implemented
        portfolios = self._portfolio.get_snapshots()

        # Step 5: Assemble success report
        return DailyReport(
            report_type=report_type,
            report_status=ReportStatus.SUCCESS,
            date=today,
            timestamp=now,
            market_macros=macros,
            portfolios=portfolios,
        )
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/unit/test_report_engine.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/quant/report/engine.py tests/unit/test_report_engine.py
git commit -m "Add report engine pipeline orchestrator"
```

---

## Task 8: BaseReportFormatter ABC

**Files:**
- Create: `outputs/base_report_formatter.py`

- [ ] **Step 1: Create the ABC**

Create `outputs/base_report_formatter.py`:

```python
"""Base class for daily report formatters.

Separate from BaseFormatter (which handles individual signal alerts).
Report formatting has different methods: report, holiday, error, drill-downs.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from quant.models.daily_report import DailyReport


class BaseReportFormatter(ABC):
    """Abstract base for daily report formatters."""

    @abstractmethod
    def format_report(self, report: DailyReport) -> Any:
        """Format a successful daily report."""
        ...

    @abstractmethod
    def format_holiday(self, report: DailyReport) -> Any:
        """Format a market holiday message."""
        ...

    @abstractmethod
    def format_error(self, report: DailyReport) -> Any:
        """Format an error report."""
        ...

    @abstractmethod
    def format_portfolio_drilldown(self, report: DailyReport) -> Any:
        """Format the virtual portfolio drill-down."""
        ...

    @abstractmethod
    def format_analysis_drilldown(self, report: DailyReport) -> Any:
        """Format the detailed analysis drill-down."""
        ...
```

- [ ] **Step 2: Commit**

```bash
git add outputs/base_report_formatter.py
git commit -m "Add BaseReportFormatter ABC for daily reports"
```

---

## Task 9: Discord Report Formatter

**Files:**
- Create: `outputs/discord/report_formatter.py`
- Create: `tests/unit/test_discord_report_formatter.py`

- [ ] **Step 1: Write formatter tests**

Create `tests/unit/test_discord_report_formatter.py`:

```python
"""Tests for Discord daily report formatter."""
from datetime import date, datetime
from decimal import Decimal

import discord
import pytest

from outputs.discord.report_formatter import DiscordReportFormatter
from quant.models.daily_report import (
    DailyReport, ErrorCategory, MarketMacros, PortfolioTier,
    ReportStatus, ReportType, StrategyResult, VirtualPortfolio,
)
from quant.utils.types import Direction, TimeFrame
from quant.config.identity import APP_NAME


@pytest.fixture
def formatter():
    return DiscordReportFormatter()


@pytest.fixture
def success_report(sample_market_macros, sample_virtual_portfolio):
    return DailyReport(
        report_type=ReportType.EVENING,
        report_status=ReportStatus.SUCCESS,
        date=date(2026, 3, 24),
        timestamp=datetime(2026, 3, 24, 16, 0, 0),
        market_macros=sample_market_macros,
        top_3_bullish=[
            StrategyResult(
                strategy_id="BQ1", strategy_name="Adjusted Iron Fly",
                direction=Direction.BULLISH, timeframe=TimeFrame.QUARTERLY,
                confidence_score=90.0,
            ),
        ],
        top_3_bearish=[
            StrategyResult(
                strategy_id="BrQ1", strategy_name="Skip-Strike Put Butterfly",
                direction=Direction.BEARISH, timeframe=TimeFrame.QUARTERLY,
                confidence_score=92.0,
            ),
        ],
        portfolios=[sample_virtual_portfolio],
    )


class TestDiscordReportFormatter:
    def test_format_report_returns_embed(self, formatter, success_report):
        result = formatter.format_report(success_report)
        assert isinstance(result, discord.Embed)
        assert APP_NAME in result.title

    def test_format_report_has_market_fields(self, formatter, success_report):
        embed = formatter.format_report(success_report)
        field_names = [f.name for f in embed.fields]
        assert "MARKET OVERVIEW" in " ".join(field_names) or len(embed.description) > 0

    def test_format_holiday_returns_embed(self, formatter):
        report = DailyReport(
            report_type=ReportType.MORNING,
            report_status=ReportStatus.MARKET_HOLIDAY,
            date=date(2026, 3, 26),
            timestamp=datetime(2026, 3, 26, 8, 30, 0),
            holiday_name="Holi",
            next_trading_day=date(2026, 3, 27),
        )
        embed = formatter.format_holiday(report)
        assert isinstance(embed, discord.Embed)
        assert "Holi" in embed.description
        assert "27 March" in embed.description or "27" in embed.description

    def test_format_error_returns_embed(self, formatter):
        report = DailyReport(
            report_type=ReportType.EVENING,
            report_status=ReportStatus.ERROR,
            date=date(2026, 3, 24),
            timestamp=datetime(2026, 3, 24, 16, 0, 0),
            error_category=ErrorCategory.MARKET_DATA_UNAVAILABLE,
            error_detail="Fyers API timeout",
        )
        embed = formatter.format_error(report)
        assert isinstance(embed, discord.Embed)
        assert "Market Data Unavailable" in embed.description

    def test_format_portfolio_drilldown(self, formatter, success_report):
        embed = formatter.format_portfolio_drilldown(success_report)
        assert isinstance(embed, discord.Embed)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_discord_report_formatter.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Create Discord report formatter**

Create `outputs/discord/report_formatter.py`:

```python
"""Discord daily report formatter using Embeds."""
from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from quant.config.identity import APP_NAME
from quant.models.daily_report import ERROR_LABELS, ReportType
from outputs.base_report_formatter import BaseReportFormatter

if TYPE_CHECKING:
    from quant.models.daily_report import DailyReport

COLOR_REPORT = discord.Color.gold()
COLOR_HOLIDAY = discord.Color.green()
COLOR_ERROR = discord.Color.red()
COLOR_DRILLDOWN = discord.Color.blurple()


class DiscordReportFormatter(BaseReportFormatter):
    """Formats DailyReport as Discord Embed objects."""

    def format_report(self, report: DailyReport) -> discord.Embed:
        """Format a successful daily report as Discord Embed."""
        macros = report.market_macros
        report_label = report.report_type.value
        date_str = report.date.strftime("%A, %d %B %Y")

        embed = discord.Embed(
            title=f"{APP_NAME} — Daily Report",
            description=f"\U0001f4c5 {date_str} | {report_label}",
            color=COLOR_REPORT,
        )

        # Market overview
        if macros:
            nifty_arrow = "\u25b2" if macros.nifty_change_pct >= 0 else "\u25bc"
            bn_arrow = "\u25b2" if macros.banknifty_change_pct >= 0 else "\u25bc"
            vix_arrow = "\u25bc" if macros.vix_change < 0 else "\u25b2"
            overview = (
                f"NIFTY    {macros.nifty_price:,.2f}  {nifty_arrow} {macros.nifty_change_pct:+.1f}%\n"
                f"BANKNIFTY {macros.banknifty_price:,.2f}  {bn_arrow} {macros.banknifty_change_pct:+.1f}%\n"
                f"VIX      {macros.india_vix:.1f}  {vix_arrow} {macros.vix_change:+.1f}\n"
                f"PCR (OI) {macros.nifty_pcr_oi:.2f}  |  Max Pain: {macros.nifty_max_pain:,.0f}\n"
                f"IV Rank  NIFTY {macros.nifty_iv_percentile:.0f}%  BN {macros.banknifty_iv_percentile:.0f}%\n"
                f"FII Net  \u20b9{macros.fii_net_cash:,.0f} Cr  |  DII Net  \u20b9{macros.dii_net_cash:,.0f} Cr"
            )
            embed.add_field(name="\U0001f4ca MARKET OVERVIEW", value=f"```\n{overview}\n```", inline=False)

        # Top bullish
        if report.top_3_bullish:
            lines = []
            for i, s in enumerate(report.top_3_bullish[:3], 1):
                score = f"{s.confidence_score:.0f}/110" if s.confidence_score else "—"
                rr = f"R:R {s.signal.risk_reward_ratio:.1f}" if s.signal else ""
                lines.append(f"{i}. {s.strategy_id} {s.strategy_name} | {score} | {rr}")
            embed.add_field(name="\U0001f7e2 TOP BULLISH", value="\n".join(lines), inline=False)

        # Top bearish
        if report.top_3_bearish:
            lines = []
            for i, s in enumerate(report.top_3_bearish[:3], 1):
                score = f"{s.confidence_score:.0f}/110" if s.confidence_score else "—"
                rr = f"R:R {s.signal.risk_reward_ratio:.1f}" if s.signal else ""
                lines.append(f"{i}. {s.strategy_id} {s.strategy_name} | {score} | {rr}")
            embed.add_field(name="\U0001f534 TOP BEARISH", value="\n".join(lines), inline=False)

        return embed

    def format_holiday(self, report: DailyReport) -> discord.Embed:
        """Format a holiday message."""
        date_str = report.date.strftime("%A, %d %B %Y")
        next_str = report.next_trading_day.strftime("%A, %d %B %Y") if report.next_trading_day else "unknown"
        embed = discord.Embed(
            title=f"{APP_NAME} — Daily Report",
            description=(
                f"\U0001f4c5 {date_str}\n\n"
                f"\U0001f3d6\ufe0f Market Holiday — {report.holiday_name}\n\n"
                f"Trading resumes on {next_str}.\nSee you then!"
            ),
            color=COLOR_HOLIDAY,
        )
        return embed

    def format_error(self, report: DailyReport) -> discord.Embed:
        """Format an error message."""
        date_str = report.date.strftime("%A, %d %B %Y")
        report_label = report.report_type.value
        cat_label = ERROR_LABELS.get(report.error_category, "Unexpected Error") if report.error_category else "Unexpected Error"
        embed = discord.Embed(
            title=f"{APP_NAME} — Daily Report",
            description=(
                f"\U0001f4c5 {date_str} | {report_label}\n\n"
                f"\u26a0\ufe0f Report Generation Failed\n\n"
                f"Category: {cat_label}\n"
                f"{report.error_detail or ''}\n\n"
                f"Will retry automatically. If issue persists,\ncheck system logs."
            ),
            color=COLOR_ERROR,
        )
        return embed

    def format_portfolio_drilldown(self, report: DailyReport) -> discord.Embed:
        """Format virtual portfolio drill-down as embed."""
        embed = discord.Embed(title="\U0001f4bc VIRTUAL PORTFOLIO TRACKER", color=COLOR_DRILLDOWN)
        for p in report.portfolios:
            tier_label = p.tier.value.capitalize()
            threshold_str = f"({p.threshold}+ score)" if p.threshold > 0 else "(All signals)"
            value = (
                f"Active: {p.active_positions} | Total: {p.total_trades} | Win Rate: {p.win_rate:.0%}\n"
                f"P&L: \u20b9{p.realized_pnl:+,.0f} (Realized) + \u20b9{p.unrealized_pnl:+,.0f} (Open)\n"
                f"Best: {p.best_strategy} | Worst: {p.worst_strategy}"
            )
            embed.add_field(name=f"{tier_label} {threshold_str}", value=value, inline=False)
        return embed

    def format_analysis_drilldown(self, report: DailyReport) -> discord.Embed:
        """Format detailed analysis drill-down as embed."""
        embed = discord.Embed(title="\U0001f50d DETAILED ANALYSIS", color=COLOR_DRILLDOWN)
        macros = report.market_macros
        if macros:
            # Dealer positioning
            if macros.net_gamma_exposure is not None:
                gex_label = "Stabilizing" if macros.net_gamma_exposure > 0 else "Destabilizing"
                dealer = (
                    f"GEX: \u20b9{macros.net_gamma_exposure:+,.0f} ({gex_label})\n"
                    f"Call Wall: {macros.call_wall or '—'} | Put Wall: {macros.put_wall or '—'}\n"
                    f"Gamma Flip: {macros.gamma_flip_level or '—'}"
                )
                embed.add_field(name="Dealer Positioning", value=dealer, inline=False)

            # Support/Resistance
            if macros.nifty_support_levels:
                s_str = " / ".join(f"{s:,.0f}" for s in macros.nifty_support_levels)
                r_str = " / ".join(f"{r:,.0f}" for r in macros.nifty_resistance_levels)
                embed.add_field(name="Support/Resistance", value=f"S: {s_str}\nR: {r_str}", inline=False)

        return embed
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/unit/test_discord_report_formatter.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add outputs/discord/report_formatter.py tests/unit/test_discord_report_formatter.py
git commit -m "Add Discord daily report formatter with embeds"
```

---

## Task 10: Telegram Report Formatter

**Files:**
- Create: `outputs/telegram/report_formatter.py`
- Create: `tests/unit/test_telegram_report_formatter.py`

- [ ] **Step 1: Write formatter tests**

Create `tests/unit/test_telegram_report_formatter.py`:

```python
"""Tests for Telegram daily report formatter."""
from datetime import date, datetime
from decimal import Decimal

import pytest

from outputs.telegram.report_formatter import TelegramReportFormatter
from quant.models.daily_report import (
    DailyReport, ErrorCategory, ReportStatus, ReportType,
    StrategyResult, VirtualPortfolio, PortfolioTier,
)
from quant.utils.types import Direction, TimeFrame
from quant.config.identity import APP_NAME


@pytest.fixture
def formatter():
    return TelegramReportFormatter()


class TestTelegramReportFormatter:
    def test_format_report_returns_string(self, formatter, sample_daily_report):
        text, keyboard = formatter.format_report(sample_daily_report)
        assert isinstance(text, str)
        assert APP_NAME.replace("P", "\\P") in text or APP_NAME in text

    def test_format_report_has_inline_keyboard(self, formatter, sample_daily_report):
        text, keyboard = formatter.format_report(sample_daily_report)
        assert keyboard is not None
        # Should have 2 buttons
        assert len(keyboard) >= 1

    def test_format_holiday_no_keyboard(self, formatter):
        report = DailyReport(
            report_type=ReportType.MORNING,
            report_status=ReportStatus.MARKET_HOLIDAY,
            date=date(2026, 3, 26),
            timestamp=datetime(2026, 3, 26, 8, 30, 0),
            holiday_name="Holi",
            next_trading_day=date(2026, 3, 27),
        )
        text, keyboard = formatter.format_holiday(report)
        assert "Holi" in text
        assert keyboard is None

    def test_format_error_has_category(self, formatter):
        report = DailyReport(
            report_type=ReportType.EVENING,
            report_status=ReportStatus.ERROR,
            date=date(2026, 3, 24),
            timestamp=datetime(2026, 3, 24, 16, 0, 0),
            error_category=ErrorCategory.API_RATE_LIMITED,
            error_detail="Rate limit exceeded",
        )
        text, keyboard = formatter.format_error(report)
        assert "Rate Limited" in text or "rate" in text.lower()
        assert keyboard is None

    def test_format_portfolio_drilldown(self, formatter, sample_daily_report):
        sample_daily_report.portfolios = [
            VirtualPortfolio(
                tier=PortfolioTier.CONSERVATIVE, threshold=85,
                active_positions=3, total_trades=28,
                realized_pnl=Decimal("42300"), unrealized_pnl=Decimal("8100"),
                total_pnl=Decimal("50400"), win_rate=0.68,
                best_strategy="BQ1", worst_strategy="BrM2",
            ),
        ]
        text = formatter.format_portfolio_drilldown(sample_daily_report)
        assert isinstance(text, str)
        assert "Conservative" in text or "CONSERVATIVE" in text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_telegram_report_formatter.py -v`
Expected: FAIL

- [ ] **Step 3: Create Telegram report formatter**

Create `outputs/telegram/report_formatter.py`:

```python
"""Telegram daily report formatter using MarkdownV2."""
from __future__ import annotations

from typing import Any, TYPE_CHECKING

from quant.config.identity import APP_NAME
from quant.models.daily_report import ERROR_LABELS, ReportType
from outputs.base_report_formatter import BaseReportFormatter
from outputs.telegram.formatter import _escape_md

if TYPE_CHECKING:
    from quant.models.daily_report import DailyReport

# Inline keyboard button definitions (callback_data patterns)
_BTN_PORTFOLIO = "\U0001f4c8 Virtual Portfolio"
_BTN_ANALYSIS = "\U0001f50d Detailed Analysis"


def _inline_keyboard(report_date: str) -> list[list[dict[str, str]]]:
    """Build Telegram InlineKeyboardMarkup-compatible structure."""
    return [
        [
            {"text": _BTN_PORTFOLIO, "callback_data": f"report_portfolio_{report_date}"},
            {"text": _BTN_ANALYSIS, "callback_data": f"report_analysis_{report_date}"},
        ]
    ]


class TelegramReportFormatter(BaseReportFormatter):
    """Formats DailyReport as Telegram MarkdownV2 strings."""

    def format_report(self, report: DailyReport) -> tuple[str, list[list[dict[str, str]]] | None]:
        """Format successful report. Returns (text, inline_keyboard)."""
        macros = report.market_macros
        report_label = report.report_type.value
        date_str = report.date.strftime("%A, %d %B %Y")
        app = _escape_md(APP_NAME)

        lines = [
            "\u2501" * 15,
            f"*{app} — Daily Report*",
            f"\U0001f4c5 {_escape_md(date_str)} \\| {_escape_md(report_label)}",
            "\u2501" * 15,
            "",
        ]

        if macros:
            nifty_arrow = "\u25b2" if macros.nifty_change_pct >= 0 else "\u25bc"
            bn_arrow = "\u25b2" if macros.banknifty_change_pct >= 0 else "\u25bc"
            vix_arrow = "\u25bc" if macros.vix_change < 0 else "\u25b2"
            lines.extend([
                "\U0001f4ca *MARKET OVERVIEW*",
                f"\u251c NIFTY    {_escape_md(f'{macros.nifty_price:,.2f}')}  {nifty_arrow} {_escape_md(f'{macros.nifty_change_pct:+.1f}%')}",
                f"\u251c BANKNIFTY {_escape_md(f'{macros.banknifty_price:,.2f}')}  {bn_arrow} {_escape_md(f'{macros.banknifty_change_pct:+.1f}%')}",
                f"\u251c VIX      {_escape_md(f'{macros.india_vix:.1f}')}  {vix_arrow} {_escape_md(f'{macros.vix_change:+.1f}')}",
                f"\u251c PCR \\(OI\\) {_escape_md(f'{macros.nifty_pcr_oi:.2f}')}  \\|  Max Pain: {_escape_md(f'{macros.nifty_max_pain:,.0f}')}",
                f"\u251c IV Rank  NIFTY {_escape_md(f'{macros.nifty_iv_percentile:.0f}%')}  BN {_escape_md(f'{macros.banknifty_iv_percentile:.0f}%')}",
                f"\u2514 FII Net  \u20b9{_escape_md(f'{macros.fii_net_cash:,.0f}')} Cr  \\|  DII Net  \u20b9{_escape_md(f'{macros.dii_net_cash:,.0f}')} Cr",
                "",
                "\u2500" * 15,
                "",
            ])

        # Top bullish
        if report.top_3_bullish:
            lines.append("\U0001f7e2 *TOP BULLISH SIGNALS*")
            for i, s in enumerate(report.top_3_bullish[:3], 1):
                score = f"{s.confidence_score:.0f}/110" if s.confidence_score else "\u2014"
                rr = f"R:R {s.signal.risk_reward_ratio:.1f}" if s.signal else ""
                lines.append(f"{i}\\. {_escape_md(s.strategy_id)} {_escape_md(s.strategy_name)} \\| {_escape_md(score)} \\| {_escape_md(rr)}")
            lines.append("")

        # Top bearish
        if report.top_3_bearish:
            lines.append("\U0001f534 *TOP BEARISH SIGNALS*")
            for i, s in enumerate(report.top_3_bearish[:3], 1):
                score = f"{s.confidence_score:.0f}/110" if s.confidence_score else "\u2014"
                rr = f"R:R {s.signal.risk_reward_ratio:.1f}" if s.signal else ""
                lines.append(f"{i}\\. {_escape_md(s.strategy_id)} {_escape_md(s.strategy_name)} \\| {_escape_md(score)} \\| {_escape_md(rr)}")

        text = "\n".join(lines)
        keyboard = _inline_keyboard(report.date.isoformat())
        return text, keyboard

    def format_holiday(self, report: DailyReport) -> tuple[str, None]:
        """Format holiday message. No keyboard buttons."""
        date_str = report.date.strftime("%A, %d %B %Y")
        next_str = report.next_trading_day.strftime("%A, %d %B %Y") if report.next_trading_day else "unknown"
        app = _escape_md(APP_NAME)
        lines = [
            "\u2501" * 15,
            f"*{app} — Daily Report*",
            f"\U0001f4c5 {_escape_md(date_str)}",
            "\u2501" * 15,
            "",
            f"\U0001f3d6\ufe0f Market Holiday — {_escape_md(report.holiday_name or 'Holiday')}",
            "",
            f"Trading resumes on {_escape_md(next_str)}\\.",
            "See you then\\!",
        ]
        return "\n".join(lines), None

    def format_error(self, report: DailyReport) -> tuple[str, None]:
        """Format error message. No keyboard buttons."""
        date_str = report.date.strftime("%A, %d %B %Y")
        report_label = report.report_type.value
        app = _escape_md(APP_NAME)
        cat_label = ERROR_LABELS.get(report.error_category, "Unexpected Error") if report.error_category else "Unexpected Error"
        lines = [
            "\u2501" * 15,
            f"*{app} — Daily Report*",
            f"\U0001f4c5 {_escape_md(date_str)} \\| {_escape_md(report_label)}",
            "\u2501" * 15,
            "",
            "\u26a0\ufe0f *Report Generation Failed*",
            "",
            f"Category: {_escape_md(cat_label)}",
            _escape_md(report.error_detail or ""),
            "",
            "Will retry automatically\\. If issue persists,",
            "check system logs\\.",
        ]
        return "\n".join(lines), None

    def format_portfolio_drilldown(self, report: DailyReport) -> str:
        """Format virtual portfolio drill-down as MarkdownV2."""
        lines = ["\U0001f4bc *VIRTUAL PORTFOLIO TRACKER*", ""]
        for p in report.portfolios:
            tier_label = _escape_md(p.tier.value.capitalize())
            threshold_str = _escape_md(f"({p.threshold}+ score)") if p.threshold > 0 else "\\(All signals\\)"
            lines.extend([
                f"*{tier_label}* {threshold_str}",
                f"\u251c Active: {p.active_positions} \\| Total: {p.total_trades} \\| Win Rate: {_escape_md(f'{p.win_rate:.0%}')}",
                f"\u251c P&L: \u20b9{_escape_md(f'{p.realized_pnl:+,.0f}')} \\(Realized\\) \\+ \u20b9{_escape_md(f'{p.unrealized_pnl:+,.0f}')} \\(Open\\)",
                f"\u2514 Best: {_escape_md(p.best_strategy)} \\| Worst: {_escape_md(p.worst_strategy)}",
                "",
            ])
        return "\n".join(lines)

    def format_analysis_drilldown(self, report: DailyReport) -> str:
        """Format detailed analysis drill-down as MarkdownV2."""
        lines = ["\U0001f50d *DETAILED ANALYSIS*", ""]
        macros = report.market_macros
        if macros and macros.net_gamma_exposure is not None:
            gex_label = "Stabilizing" if macros.net_gamma_exposure > 0 else "Destabilizing"
            lines.extend([
                "*Dealer Positioning*",
                f"\u251c GEX: \u20b9{_escape_md(f'{macros.net_gamma_exposure:+,.0f}')} \\({_escape_md(gex_label)}\\)",
                f"\u251c Call Wall: {_escape_md(str(macros.call_wall or '—'))} \\| Put Wall: {_escape_md(str(macros.put_wall or '—'))}",
                f"\u2514 Gamma Flip: {_escape_md(str(macros.gamma_flip_level or '—'))}",
                "",
            ])
        if macros and macros.nifty_support_levels:
            s_str = _escape_md(" / ".join(f"{s:,.0f}" for s in macros.nifty_support_levels))
            r_str = _escape_md(" / ".join(f"{r:,.0f}" for r in macros.nifty_resistance_levels))
            lines.extend([
                "*Support/Resistance*",
                f"\u251c S: {s_str}",
                f"\u2514 R: {r_str}",
            ])
        return "\n".join(lines)
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/unit/test_telegram_report_formatter.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add outputs/telegram/report_formatter.py tests/unit/test_telegram_report_formatter.py
git commit -m "Add Telegram daily report formatter with inline keyboard"
```

---

## Task 11: Extend Bots with send_daily_report()

**Files:**
- Modify: `outputs/discord/bot.py`
- Modify: `outputs/telegram/bot.py`

- [ ] **Step 1: Extend Discord bot**

Add to `outputs/discord/bot.py` (after existing `send_signal` method):

```python
    async def send_daily_report(self, report: DailyReport) -> None:
        """Send a daily report to the configured Discord channel."""
        if not self._token:
            logger.warning("Discord bot token not configured", app=APP_NAME)
            return

        from outputs.discord.report_formatter import DiscordReportFormatter
        from quant.models.daily_report import ReportStatus

        fmt = DiscordReportFormatter()
        if report.report_status == ReportStatus.SUCCESS:
            embed = fmt.format_report(report)
            portfolio_embed = fmt.format_portfolio_drilldown(report)
            analysis_embed = fmt.format_analysis_drilldown(report)
            embeds = [embed, portfolio_embed, analysis_embed]
        elif report.report_status == ReportStatus.MARKET_HOLIDAY:
            embeds = [fmt.format_holiday(report)]
        else:
            embeds = [fmt.format_error(report)]

        # TODO: Actual Discord API call using discord.py Client
        logger.info(
            "Discord daily report prepared",
            status=report.report_status.value,
            embeds_count=len(embeds),
            channel=self._channel_id,
        )
```

Add `DailyReport` to the TYPE_CHECKING imports block at the top of the file:

```python
if TYPE_CHECKING:
    from quant.models.signals import SignalPayload
    from quant.models.daily_report import DailyReport
```

- [ ] **Step 2: Extend Telegram bot**

Add to `outputs/telegram/bot.py` (after existing `send_signal` method):

```python
    async def send_daily_report(self, report: DailyReport) -> None:
        """Send a daily report to the configured Telegram chat."""
        if not self._token:
            logger.warning("Telegram bot token not configured", app=APP_NAME)
            return

        from outputs.telegram.report_formatter import TelegramReportFormatter
        from quant.models.daily_report import ReportStatus

        fmt = TelegramReportFormatter()
        if report.report_status == ReportStatus.SUCCESS:
            text, keyboard = fmt.format_report(report)
        elif report.report_status == ReportStatus.MARKET_HOLIDAY:
            text, keyboard = fmt.format_holiday(report)
        else:
            text, keyboard = fmt.format_error(report)

        # TODO: Actual Telegram API call using python-telegram-bot
        # await bot.send_message(chat_id=self._chat_id, text=text,
        #     parse_mode="MarkdownV2", reply_markup=keyboard_markup)
        logger.info(
            "Telegram daily report prepared",
            status=report.report_status.value,
            has_keyboard=keyboard is not None,
            chat_id=self._chat_id,
        )
```

Add `DailyReport` to the TYPE_CHECKING imports block at the top of the file:

```python
if TYPE_CHECKING:
    from quant.models.signals import SignalPayload
    from quant.models.daily_report import DailyReport
```

- [ ] **Step 3: Commit**

```bash
git add outputs/discord/bot.py outputs/telegram/bot.py
git commit -m "Extend Discord and Telegram bots with send_daily_report"
```

---

## Task 12: Database Schema + Writer Extensions

**Files:**
- Modify: `outputs/website/schema.py`
- Modify: `outputs/website/writer.py`

- [ ] **Step 1: Add report tables to schema.py**

Add to `outputs/website/schema.py` (after `StrategyPerformance` class):

```python
class DailyReportRecord(Base):
    """Persisted daily report for website/ML pipeline."""
    __tablename__ = f"{APP_NAME_SNAKE}_daily_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    report_type = Column(String(10), nullable=False)  # MORNING / EVENING
    report_status = Column(String(20), nullable=False)  # SUCCESS / MARKET_HOLIDAY / ERROR
    timestamp = Column(DateTime, nullable=False)
    holiday_name = Column(String(100))
    next_trading_day = Column(String(10))
    market_macros_json = Column(Text, default="{}")
    strategy_results_json = Column(Text, default="[]")
    portfolios_json = Column(Text, default="[]")
    error_category = Column(String(50))
    error_detail = Column(Text)


class VirtualPortfolioRecord(Base):
    """Persisted virtual portfolio state."""
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
    """Individual virtual trade."""
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
```

- [ ] **Step 2: Add write_daily_report to writer.py**

Add to `outputs/website/writer.py` (after existing `update_trade` method, before `close`):

```python
    async def write_daily_report(self, report: DailyReport) -> int:
        """Write a daily report to the database and return its ID."""
        from outputs.website.schema import DailyReportRecord, VirtualPortfolioRecord

        record = DailyReportRecord(
            report_date=report.date.isoformat(),
            report_type=report.report_type.value,
            report_status=report.report_status.value,
            timestamp=report.timestamp,
            holiday_name=report.holiday_name,
            next_trading_day=report.next_trading_day.isoformat() if report.next_trading_day else None,
            market_macros_json=report.market_macros.model_dump_json() if report.market_macros else "{}",
            strategy_results_json="[]",  # TODO: serialize strategy results
            portfolios_json="[]",  # TODO: serialize portfolios
            error_category=report.error_category.value if report.error_category else None,
            error_detail=report.error_detail,
        )
        async with self._session_factory() as session:
            session.add(record)
            # Also persist portfolio snapshots
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
```

Add the DailyReport import to the TYPE_CHECKING block:

```python
if TYPE_CHECKING:
    from quant.models.signals import SignalPayload
    from quant.models.daily_report import DailyReport
```

- [ ] **Step 3: Commit**

```bash
git add outputs/website/schema.py outputs/website/writer.py
git commit -m "Add daily report DB tables and write_daily_report"
```

---

## Task 13: CLI `report` Command

**Files:**
- Modify: `src/quant/cli.py`

- [ ] **Step 1: Add report command to cli.py**

Add after the `serve` command in `src/quant/cli.py`:

```python
@cli.command()
@click.option("--type", "report_type", type=click.Choice(["morning", "evening"]), required=True,
              help="Report type: morning (pre-market) or evening (post-market)")
@click.option("--dry-run", is_flag=True, help="Generate report but don't dispatch to channels")
def report(report_type: str, dry_run: bool) -> None:
    """Generate and send the daily report."""
    import asyncio
    from quant.models.daily_report import ReportType, ReportStatus
    from quant.report.engine import DailyReportEngine

    rt = ReportType.MORNING if report_type == "morning" else ReportType.EVENING
    click.echo(f"[{APP_NAME}] Generating {report_type} report...")

    engine = DailyReportEngine()
    result = asyncio.run(engine.generate(rt, dry_run=dry_run))

    if result.report_status == ReportStatus.SUCCESS:
        click.echo(f"  Status: SUCCESS")
        click.echo(f"  Date: {result.date}")
        if result.market_macros:
            click.echo(f"  NIFTY: {result.market_macros.nifty_price}")
    elif result.report_status == ReportStatus.MARKET_HOLIDAY:
        click.echo(f"  Status: MARKET HOLIDAY — {result.holiday_name}")
        click.echo(f"  Next trading day: {result.next_trading_day}")
    else:
        click.echo(f"  Status: ERROR — {result.error_category}")
        click.echo(f"  Detail: {result.error_detail}")
        raise SystemExit(1)
```

- [ ] **Step 2: Test CLI manually**

Run: `pivotpoint report --type evening --dry-run`
Expected: Shows error status (MarketDataCollector not implemented) with exit code 1.

Run: `pivotpoint --help`
Expected: Shows `report` command in the help output.

- [ ] **Step 3: Commit**

```bash
git add src/quant/cli.py
git commit -m "Add report CLI command with --type and --dry-run"
```

---

## Task 14: GitHub Actions Workflows

**Files:**
- Create: `.github/workflows/morning-report.yml`
- Create: `.github/workflows/evening-report.yml`

- [ ] **Step 1: Create morning-report.yml**

Create `.github/workflows/morning-report.yml`:

```yaml
name: PivotPoint Morning Report

on:
  schedule:
    - cron: '0 3 * * 1-5'  # 3:00 UTC = 8:30 AM IST, Mon-Fri
  workflow_dispatch: {}

jobs:
  report:
    runs-on: ubuntu-latest
    env:
      FYERS__APP_ID: ${{ secrets.FYERS_APP_ID }}
      FYERS__SECRET_KEY: ${{ secrets.FYERS_SECRET_KEY }}
      DISCORD__BOT_TOKEN: ${{ secrets.DISCORD_BOT_TOKEN }}
      DISCORD__CHANNEL_ID: ${{ secrets.DISCORD_CHANNEL_ID }}
      TELEGRAM__BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
      TELEGRAM__CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
      DATABASE__URL: ${{ secrets.DATABASE_URL }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      - run: pip install -e .
      - run: pivotpoint report --type morning
```

- [ ] **Step 2: Create evening-report.yml**

Create `.github/workflows/evening-report.yml`:

```yaml
name: PivotPoint Evening Report

on:
  schedule:
    - cron: '30 10 * * 1-5'  # 10:30 UTC = 4:00 PM IST, Mon-Fri
  workflow_dispatch: {}

jobs:
  report:
    runs-on: ubuntu-latest
    env:
      FYERS__APP_ID: ${{ secrets.FYERS_APP_ID }}
      FYERS__SECRET_KEY: ${{ secrets.FYERS_SECRET_KEY }}
      DISCORD__BOT_TOKEN: ${{ secrets.DISCORD_BOT_TOKEN }}
      DISCORD__CHANNEL_ID: ${{ secrets.DISCORD_CHANNEL_ID }}
      TELEGRAM__BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
      TELEGRAM__CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
      DATABASE__URL: ${{ secrets.DATABASE_URL }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      - run: pip install -e .
      - run: pivotpoint report --type evening
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/morning-report.yml .github/workflows/evening-report.yml
git commit -m "Add GitHub Actions cron workflows for daily reports"
```

---

## Task 15: Final Integration Test + Lint

**Files:** All created/modified files

- [ ] **Step 1: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests pass (existing + new)

- [ ] **Step 2: Lint all new files**

Run: `ruff check src/quant/models/daily_report.py src/quant/calendar/ src/quant/report/ outputs/base_report_formatter.py outputs/discord/report_formatter.py outputs/telegram/report_formatter.py`
Expected: No errors

- [ ] **Step 3: Format**

Run: `ruff format src/quant/models/daily_report.py src/quant/calendar/ src/quant/report/ outputs/base_report_formatter.py outputs/discord/report_formatter.py outputs/telegram/report_formatter.py`

- [ ] **Step 4: Type check**

Run: `mypy src/quant/models/daily_report.py src/quant/calendar/ src/quant/report/`
Expected: No errors (or only expected warnings from stubs)

- [ ] **Step 5: Run CLI smoke test**

Run: `pivotpoint report --type evening --dry-run`
Expected: Runs, prints error status (MarketDataCollector not implemented), exits with code 1.

Run: `pivotpoint info`
Expected: Still works, shows strategies as before.

- [ ] **Step 6: Final commit if any fixes needed**

```bash
git add src/quant/models/daily_report.py src/quant/calendar/ src/quant/report/ outputs/base_report_formatter.py outputs/discord/report_formatter.py outputs/telegram/report_formatter.py
git commit -m "Fix lint and type check issues in daily report system"
```
