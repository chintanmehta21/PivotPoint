# Daily Report Output System — Design Spec

**Date:** 2026-03-23
**Status:** Approved
**Scope:** Automated daily reports to Discord + Telegram with market macros, strategy results, virtual portfolios, and holiday/error handling.

---

## 1. Overview

PivotPoint needs an automated daily reporting system that delivers market intelligence and strategy results to Discord and Telegram on every working day. The system runs twice daily (morning preview + evening summary) via GitHub Actions cron, with zero manual intervention.

### Three Report States

| State | Trigger | Content |
|-------|---------|---------|
| **SUCCESS** | Normal trading day, data available | Full report: macros + top-3 strategies + drill-down buttons |
| **MARKET_HOLIDAY** | NSE closed (layered holiday detection) | Holiday name + next trading day |
| **ERROR** | Any failure during pipeline | Categorized error message |

---

## 2. Data Model

All models live in `src/quant/models/daily_report.py`, following existing Pydantic patterns.

### 2.1 Enums

```python
class ReportType(str, Enum):
    MORNING = "MORNING"     # Pre-market preview (8:30 AM IST)
    EVENING = "EVENING"     # Post-market summary (4:00 PM IST)

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

class PortfolioTier(str, Enum):
    CONSERVATIVE = "CONSERVATIVE"
    MODERATE = "MODERATE"
    AGGRESSIVE = "AGGRESSIVE"
```

All enums follow the existing codebase pattern where name == value (consistent with `Direction`, `TimeFrame`, `SignalType`, etc.). `ErrorCategory` and its human-readable label mapping both live in `models/daily_report.py` (no separate `error_categories.py` file).

### 2.2 MarketMacros

Stores the full market overview. All fields populated from Fyers API + NSE data. The formatter selects which subset to display; the full model is persisted to DB for ML/backtesting pipelines.

```python
class MarketMacros(BaseModel):
    """Full market snapshot. Formatter displays only the 'displayed' subset."""

    # --- DISPLAYED in main report ---
    nifty_price: Decimal
    nifty_change_pct: float
    banknifty_price: Decimal
    banknifty_change_pct: float
    india_vix: float
    vix_change: float
    nifty_pcr_oi: float
    nifty_max_pain: Decimal
    banknifty_max_pain: Decimal
    nifty_iv_percentile: float          # vs 1yr history
    banknifty_iv_percentile: float
    fii_net_cash: Decimal               # in crores
    dii_net_cash: Decimal

    # --- STORED for ML feature store / detailed drill-down (Optional) ---
    # Breadth
    advance_decline_ratio: float | None = None
    pct_above_20dma: float | None = None
    pct_above_50dma: float | None = None
    pct_above_200dma: float | None = None

    # Options analytics
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

    # Gamma/dealer positioning
    net_gamma_exposure: Decimal | None = None
    call_wall: Decimal | None = None
    put_wall: Decimal | None = None
    gamma_flip_level: Decimal | None = None
    vanna_exposure: float | None = None
    charm_exposure: float | None = None

    # Institutional flow
    fii_net_derivatives: Decimal | None = None
    dii_net_derivatives: Decimal | None = None
    fii_index_futures_long_short_ratio: float | None = None

    # Technical
    nifty_support_levels: list[Decimal] = Field(default_factory=list)    # 3 levels
    nifty_resistance_levels: list[Decimal] = Field(default_factory=list)
    supertrend_signal: str | None = None        # "BUY" / "SELL"
    nifty_rsi: float | None = None
    nifty_macd_state: str | None = None         # "BULLISH" / "BEARISH" / "NEUTRAL"

    # Rolling vols (ML features)
    realized_vol_5d: float | None = None
    realized_vol_10d: float | None = None
    realized_vol_20d: float | None = None
    realized_vol_60d: float | None = None
    iv_rv_spread: float | None = None
    pcr_momentum: float | None = None
    skew_slope_velocity: float | None = None
    gamma_flip_proximity: float | None = None
```

Required fields are the "displayed" subset (always populated from Fyers API). Optional fields are the ML feature store (populated when data sources are available, gracefully absent otherwise).

### 2.3 StrategyResult

```python
class StrategyResult(BaseModel):
    strategy_id: str              # e.g., "BW1", "BrQ1"
    strategy_name: str
    direction: Direction          # BULLISH or BEARISH
    timeframe: TimeFrame
    signal: SignalPayload | None  # None = no signal triggered
    confidence_score: float | None
    error: str | None             # If this strategy errored
```

### 2.4 VirtualPortfolio

Three tiers tracked independently:

| Tier | Threshold | Description |
|------|-----------|-------------|
| Conservative | 85+ score | Only highest-conviction signals |
| Moderate | 75+ score | Balanced risk/reward |
| Aggressive | All signals | Everything that triggers |

```python
class VirtualPortfolio(BaseModel):
    tier: PortfolioTier               # CONSERVATIVE / MODERATE / AGGRESSIVE
    threshold: int                    # 85, 75, 0
    active_positions: int
    total_trades: int
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    total_pnl: Decimal
    win_rate: float
    best_strategy: str                # strategy_id with best P&L
    worst_strategy: str

class VirtualTradeRecord(BaseModel):
    """Individual virtual trade for DB persistence."""
    trade_id: str                     # UUID
    tier: PortfolioTier
    strategy_id: str
    direction: Direction
    entry_date: date
    entry_price: Decimal
    exit_date: date | None = None
    exit_price: Decimal | None = None
    status: str                       # "OPEN" / "CLOSED"
    realized_pnl: Decimal | None = None
    signal_payload: SignalPayload     # Full signal for audit trail
```

### 2.5 DailyReport (Root Model)

```python
class DailyReport(BaseModel):
    report_type: ReportType
    report_status: ReportStatus
    date: date
    timestamp: datetime
    holiday_name: str | None          # e.g., "Holi" if holiday
    next_trading_day: date | None     # populated if holiday
    market_macros: MarketMacros | None
    strategy_results: list[StrategyResult] = Field(default_factory=list)
    top_3_bullish: list[StrategyResult] = Field(default_factory=list)
    top_3_bearish: list[StrategyResult] = Field(default_factory=list)
    portfolios: list[VirtualPortfolio] = Field(default_factory=list)
    error_category: ErrorCategory | None = None
    error_detail: str | None = None
```

---

## 3. Message Layouts

> **Note:** All instances of "PivotPoint" in the layout mockups below represent `{APP_NAME}` and must use the import from `quant.config.identity`. Never hardcode the app name.

### 3.1 Normal Report (SUCCESS)

Main message (~15 lines, sent as single message):

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━
𝗣𝗶𝘃𝗼𝘁𝗣𝗼𝗶𝗻𝘁 — Daily Report
📅 Monday, 24 March 2026 | EVENING
━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 MARKET OVERVIEW
├ NIFTY    22,450.30  ▲ +1.2%
├ BANKNIFTY 48,120.50  ▼ -0.4%
├ VIX      14.8  ▼ -0.6
├ PCR (OI) 1.12  │  Max Pain: 22,500
├ IV Rank  NIFTY 42%  BN 38%
└ FII Net  ₹-1,240 Cr  │  DII Net  ₹+890 Cr

─────────────────────────────

🟢 TOP BULLISH SIGNALS
1. BQ1 Adjusted Iron Fly │ 90/110 │ R:R 4.2
2. BM1 Modified Butterfly │ 85/110 │ R:R 3.8
3. BW1 Call Ratio Backspread │ 82/110 │ R:R 2.9

🔴 TOP BEARISH SIGNALS
1. BrQ1 Skip-Strike Put Butterfly │ 92/110 │ R:R 5.1
2. BrQ2 Bear Put Condor │ 87/110 │ R:R 3.5
3. BrM1 Bearish Jade Lizard │ 80/110 │ R:R 2.7

> **Confidence scale:** Scores are out of 110 (the strategy scoring system defined in each strategy class). Virtual portfolio tier thresholds (85, 75, 0) use this same 0-110 scale.
```

**Telegram:** 2 inline buttons below message → `[📈 Virtual Portfolio]` `[🔍 Detailed Analysis]`
**Discord:** 2 expandable embeds attached to the main embed

### 3.2 Drill-Down: Virtual Portfolio

```
💼 VIRTUAL PORTFOLIO TRACKER

Conservative (85+ score)
├ Active: 3 │ Total: 28 │ Win Rate: 68%
├ P&L: ₹+42,300 (Realized) + ₹+8,100 (Open)
└ Best: BQ1 │ Worst: BrM2

Moderate (75+ score)
├ Active: 5 │ Total: 51 │ Win Rate: 61%
├ P&L: ₹+67,800 (Realized) + ₹-3,200 (Open)
└ Best: BrQ1 │ Worst: BrW3

Aggressive (All signals)
├ Active: 8 │ Total: 89 │ Win Rate: 54%
├ P&L: ₹+31,100 (Realized) + ₹-12,400 (Open)
└ Best: BrQ1 │ Worst: BrM3
```

### 3.3 Drill-Down: Detailed Analysis

```
🔍 DETAILED ANALYSIS

Greeks Exposure (Net Portfolio)
├ Δ Delta: -0.42 │ Γ Gamma: +0.08
├ ν Vega: -12.3 │ Θ Theta: +45.6
└ IV Rank: 42nd percentile

Dealer Positioning
├ GEX: +₹2.1B (Stabilizing)
├ Call Wall: 22,600 │ Put Wall: 22,200
└ Gamma Flip: 22,350

Support/Resistance
├ S: 22,280 / 22,150 / 22,000
└ R: 22,550 / 22,650 / 22,800
```

### 3.4 Holiday Message

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━
𝗣𝗶𝘃𝗼𝘁𝗣𝗼𝗶𝗻𝘁 — Daily Report
📅 Wednesday, 26 March 2026
━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏖️ Market Holiday — Holi

Trading resumes on Thursday, 27 March 2026.
See you then!
```

### 3.5 Error Message

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━
𝗣𝗶𝘃𝗼𝘁𝗣𝗼𝗶𝗻𝘁 — Daily Report
📅 Monday, 24 March 2026 | EVENING
━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ Report Generation Failed

Category: Market Data Unavailable
12/14 strategies evaluated successfully.

Will retry automatically. If issue persists,
check system logs.
```

**6 predefined error categories + catch-all:**

| Category | Human-Readable | When |
|----------|---------------|------|
| `MARKET_DATA_UNAVAILABLE` | Market Data Unavailable | Fyers API down/timeout |
| `STRATEGY_EVALUATION_FAILED` | Strategy Evaluation Failed | One or more strategies errored |
| `HOLIDAY_CHECK_FAILED` | Holiday Check Failed | Couldn't determine if market is open |
| `API_RATE_LIMITED` | API Rate Limited | NSE/Fyers rate limit hit |
| `AUTHENTICATION_EXPIRED` | Authentication Expired | Fyers/bot tokens need refresh |
| `DISPATCH_FAILED` | Report Dispatch Failed | Report generated but couldn't send |
| `UNKNOWN_ERROR` | Unexpected Error | Catch-all for everything else |

Error messages include partial success info when available (e.g., "12/14 strategies evaluated").

---

## 4. File Structure

### New Files

```
src/quant/
├── models/
│   └── daily_report.py              # DailyReport, MarketMacros, VirtualPortfolio, VirtualTradeRecord,
│                                     # StrategyResult, ReportType, ReportStatus, ErrorCategory,
│                                     # PortfolioTier, ERROR_LABELS dict
├── config/
│   └── holidays.yaml                 # Manual override fallback
├── calendar/
│   ├── __init__.py
│   ├── holiday_checker.py           # Layered: exchange_calendars → NSE API → yaml fallback
│   └── market_hours.py              # IST trading hours, pre/post market windows
├── report/
│   ├── __init__.py
│   ├── engine.py                    # DailyReportEngine - orchestrates the full pipeline
│   ├── market_data_collector.py     # Fetches all macro metrics from Fyers API
│   └── portfolio_tracker.py         # 3-tier virtual portfolio simulation

outputs/
├── base_report_formatter.py         # NEW - BaseReportFormatter ABC (format_report, format_holiday, format_error)
├── discord/
│   ├── report_formatter.py          # NEW - extends BaseReportFormatter → Discord Embeds
│   └── bot.py                       # Extended with send_daily_report()
├── telegram/
│   ├── report_formatter.py          # NEW - extends BaseReportFormatter → MarkdownV2 + inline keyboard
│   └── bot.py                       # Extended with send_daily_report()
└── website/
    ├── schema.py                    # Extended with DailyReportRecord, VirtualPortfolioRecord
    └── writer.py                    # Extended with write_daily_report()

.github/
└── workflows/
    ├── morning-report.yml           # Cron: 3:00 UTC (8:30 AM IST)
    └── evening-report.yml           # Cron: 10:30 UTC (4:00 PM IST)
```

### Modified Files

- `src/quant/cli.py` — new `report` command with `--type morning|evening` and `--dry-run`
- `outputs/discord/bot.py` — add `send_daily_report(report: DailyReport)` method
- `outputs/telegram/bot.py` — add `send_daily_report(report: DailyReport)` method
- `outputs/base_report_formatter.py` — NEW `BaseReportFormatter` ABC
- `outputs/website/schema.py` — add `DailyReportRecord`, `VirtualPortfolioRecord`, `VirtualTradeRecord` tables
- `outputs/website/writer.py` — add `write_daily_report()` method
- `pyproject.toml` — add dependencies: `exchange_calendars`, `python-telegram-bot`, `discord.py`, `pyyaml`, `httpx`

---

## 5. Holiday Checker (Layered Robustness)

Lives in `src/quant/calendar/holiday_checker.py`.

```
Layer 1: Weekend check (Saturday/Sunday → always holiday)
    ↓ if weekday
Layer 2: exchange_calendars XBOM.is_session(date)
    ↓ if not a session → HOLIDAY (with holiday name lookup)
    ↓ if is a session → continue to verify
Layer 3: NSE API fetch (once daily, cached in memory)
    → GET https://www.nseindia.com/api/holiday-master?type=trading
    ↓ if API confirms open → TRADING DAY
    ↓ if API confirms closed → HOLIDAY (surprise/ad-hoc closure)
    ↓ if API fails → trust Layer 2 result
Layer 4: holidays.yaml override (checked last, can force HOLIDAY or OPEN)
```

### holidays.yaml Format

```yaml
# Manual overrides for holiday checker
# Use when exchange_calendars is wrong or NSE announces surprise holidays
overrides:
  - date: "2026-03-26"
    status: HOLIDAY         # HOLIDAY or OPEN
    name: "Holi"
  - date: "2026-11-08"
    status: HOLIDAY
    name: "Diwali Laxmi Pujan"
    muhurat_trading: true   # Special session flag for future use
```

### Key Methods

```python
class HolidayChecker:
    def is_trading_day(self, date: date) -> bool
    def get_holiday_name(self, date: date) -> str | None
    def get_next_trading_day(self, date: date) -> date
    def get_previous_trading_day(self, date: date) -> date
```

---

## 6. Report Engine Pipeline

`src/quant/report/engine.py` — single orchestrator class.

```python
class DailyReportEngine:
    async def generate(self, report_type: ReportType) -> DailyReport:
        """
        Full pipeline:
        1. Check if today is a trading day
           → If holiday: return DailyReport(status=HOLIDAY, holiday_name=..., next_trading_day=...)
        2. Fetch market data (MarketDataCollector)
           → Populates MarketMacros
        3. Run strategy scanner (existing StrategyScanner)
           → Populates strategy_results, top_3_bullish, top_3_bearish
        4. Update virtual portfolios (PortfolioTracker)
           → Populates portfolios (3 tiers)
        5. Persist to database (DatabaseWriter)
        6. Dispatch to channels (Discord + Telegram)

        Any step failure → catch, categorize, return DailyReport(status=ERROR, ...)
        Partial failures (e.g., 12/14 strategies) → still send partial report
        """
```

### Error Handling Strategy

- Each pipeline step is wrapped in try/except
- Errors are categorized into one of the 6 predefined categories
- Partial success is preserved: if market data succeeds but 2 strategies fail, the report includes the 12 successful results + an error note
- Dispatch failure (can't send to Discord/Telegram) is logged but doesn't affect DB persistence

### Retry Policy

Application-level retry for transient failures:

| Error Category | Retryable | Max Retries | Backoff |
|---|---|---|---|
| `MARKET_DATA_UNAVAILABLE` | Yes | 3 | 30s, 60s, 120s (exponential) |
| `API_RATE_LIMITED` | Yes | 3 | 60s, 120s, 240s (longer backoff) |
| `STRATEGY_EVALUATION_FAILED` | No | — | Send partial report immediately |
| `HOLIDAY_CHECK_FAILED` | No | — | Default to Layer 2 result, send report |
| `AUTHENTICATION_EXPIRED` | No | — | Send error report, requires manual token refresh |
| `DISPATCH_FAILED` | Yes | 2 | 15s, 30s |
| `UNKNOWN_ERROR` | No | — | Send error report immediately |

Non-retryable errors send the error message immediately rather than waiting.

### Morning vs Evening Content Differences

Both report types use the same `DailyReport` model but populate different data:

| Field | Morning (8:30 AM IST) | Evening (4:00 PM IST) |
|---|---|---|
| Market macros | Previous close data + pre-market indicators | Current day's close data |
| Strategy results | Strategies to watch (based on pre-market conditions) | Actual signals triggered during the day |
| Top 3 bullish/bearish | Ranked by previous day's momentum + current setup | Ranked by today's actual confidence scores |
| Virtual portfolios | Snapshot of open positions + unrealized P&L | Updated with today's realized + unrealized P&L |
| Drill-down: Greeks | Previous day's closing Greeks | Current day's closing Greeks |
| Drill-down: Dealer | Overnight GEX/positioning changes | End-of-day positioning |

---

## 7. Virtual Portfolio Tracker

`src/quant/report/portfolio_tracker.py`

Simulates three portfolios by assuming all signals above the tier's confidence threshold are "executed" at the signal's entry price.

### Mechanics

- On ENTRY signal with `confidence_score >= threshold`: open virtual position at signal's suggested entry
- On EXIT signal for an open position: close at signal's exit price, realize P&L
- Unrealized P&L: mark-to-market using current underlying price vs entry
- State persisted to DB (`VirtualPortfolioRecord` + `VirtualTradeRecord`)
- Win rate = closed trades with positive P&L / total closed trades

### Three Tiers

| Tier | Threshold | Risk Profile |
|------|-----------|-------------|
| Conservative | confidence >= 85 | Only top-rated signals |
| Moderate | confidence >= 75 | Balanced |
| Aggressive | confidence >= 0 | All triggered signals |

---

## 8. Platform-Specific Formatting

### 8.0 BaseReportFormatter (`outputs/base_report_formatter.py`)

New ABC alongside the existing `BaseFormatter` (which handles signal alerts). Report formatting is a separate concern with different methods.

```python
class BaseReportFormatter(ABC):
    """Base class for daily report formatters. Separate from BaseFormatter (signal alerts)."""

    @abstractmethod
    def format_report(self, report: DailyReport) -> Any:
        """Format a successful daily report."""

    @abstractmethod
    def format_holiday(self, report: DailyReport) -> Any:
        """Format a market holiday message."""

    @abstractmethod
    def format_error(self, report: DailyReport) -> Any:
        """Format an error report."""

    @abstractmethod
    def format_portfolio_drilldown(self, report: DailyReport) -> Any:
        """Format the virtual portfolio drill-down."""

    @abstractmethod
    def format_analysis_drilldown(self, report: DailyReport) -> Any:
        """Format the detailed analysis drill-down."""
```

### 8.1 Discord (`outputs/discord/report_formatter.py`)

- Main report: `discord.Embed` with color-coded (gold for report)
- Bold title using Discord markdown (`**PivotPoint — Daily Report**`)
- Date with calendar emoji in description
- Market overview, bullish, bearish as embed fields
- 2 additional embeds for drill-downs (Virtual Portfolio + Detailed Analysis) — sent as separate embeds in the same message, collapsible via Discord's native embed behavior
- Holiday: single embed with beach emoji, green color
- Error: single embed with warning emoji, red color
- Uses `APP_NAME` from `quant.config.identity` — never hardcoded

### 8.2 Telegram (`outputs/telegram/report_formatter.py`)

- Main report: MarkdownV2 formatted string with `_escape_md()` helper (existing pattern)
- Bold title using Telegram MarkdownV2 (`*PivotPoint — Daily Report*`)
- 2 inline keyboard buttons via `InlineKeyboardMarkup`:
  - `📈 Virtual Portfolio` → callback_data: `report_portfolio_{date}`
  - `🔍 Detailed Analysis` → callback_data: `report_analysis_{date}`
- Button callbacks handled by TelegramAlertBot — sends drill-down as reply/edit
- Holiday: plain MarkdownV2 message, no buttons
- Error: plain MarkdownV2 message, no buttons
- Uses `APP_NAME` from `quant.config.identity` — never hardcoded

---

## 9. Automation (GitHub Actions)

### 9.1 Morning Report (`morning-report.yml`)

```yaml
name: PivotPoint Morning Report
on:
  schedule:
    - cron: '0 3 * * 1-5'  # 3:00 UTC = 8:30 AM IST, Mon-Fri
  workflow_dispatch: {}      # Manual trigger for testing

jobs:
  report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e ".[dev]"
      - run: pivotpoint report --type morning
    env:
      FYERS__APP_ID: ${{ secrets.FYERS_APP_ID }}
      FYERS__SECRET_KEY: ${{ secrets.FYERS_SECRET_KEY }}
      DISCORD__BOT_TOKEN: ${{ secrets.DISCORD_BOT_TOKEN }}
      DISCORD__CHANNEL_ID: ${{ secrets.DISCORD_CHANNEL_ID }}
      TELEGRAM__BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
      TELEGRAM__CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
      DATABASE__URL: ${{ secrets.DATABASE_URL }}
```

### 9.2 Evening Report (`evening-report.yml`)

Identical structure, cron: `'30 10 * * 1-5'` (10:30 UTC = 4:00 PM IST).

### 9.3 Key Design Decisions

- **Separate workflow files** — independent failure/retry, independent logs
- **Mon-Fri only** (`1-5`) — weekend filter at cron level, holiday check at application level
- **`workflow_dispatch`** — allows manual trigger for testing without waiting for cron
- **Secrets via GitHub** — all credentials stored as repository secrets, injected via env vars matching `pydantic-settings` nested delimiter (`FYERS__APP_ID` → `settings.fyers.app_id`)
- **No Vercel involvement in cron** — GitHub Actions handles scheduling; Vercel handles website deployment only (future dynamic site)
- **Cron delay tolerance** — GitHub Actions cron can be delayed up to 15 minutes. Morning report at 8:30 AM IST (market opens 9:15) and evening report at 4:00 PM IST (market closes 3:30) both have comfortable tolerances. Report timestamps use actual execution time, not scheduled time

---

## 10. CLI Extension

New `report` command added to existing `src/quant/cli.py`:

```python
@cli.command()
@click.option("--type", "report_type", type=click.Choice(["morning", "evening"]), required=True)
@click.option("--dry-run", is_flag=True, help="Generate report but don't send to channels")
def report(report_type: str, dry_run: bool) -> None:
    """Generate and send the daily report."""
```

- `--dry-run` generates the report, prints to console, persists to DB, but skips Discord/Telegram dispatch
- Exit code 0 on SUCCESS or HOLIDAY, exit code 1 on ERROR (for GitHub Actions failure detection)

---

## 11. Dependencies

New packages to add to `pyproject.toml`:

| Package | Purpose |
|---------|---------|
| `exchange_calendars` | Holiday detection (Layer 2) |
| `discord.py` | Discord bot API |
| `python-telegram-bot` | Telegram bot API + inline keyboards |
| `pyyaml` | holidays.yaml parsing |
| `httpx` | NSE API calls (async, for holiday Layer 3) |

---

## 12. Testing Strategy

- **Unit tests** for `HolidayChecker` — mock each layer, test fallback behavior
- **Unit tests** for `DailyReportEngine` — mock market data, verify report assembly
- **Unit tests** for formatters — verify Discord embed structure, Telegram MarkdownV2 escaping
- **Unit tests** for `PortfolioTracker` — verify P&L calculation across tiers
- **Integration test** for full pipeline with `--dry-run`
- **Fixtures** in `tests/conftest.py`: `sample_daily_report`, `sample_market_macros`, `sample_virtual_portfolio`

---

## 13. Future Considerations

- **Dynamic website** — DailyReportRecord in DB is query-ready for a Next.js dashboard
- **ML pipeline** — MarketMacros stores all features needed for backtesting and model training
- **Muhurat trading** — holidays.yaml supports `muhurat_trading: true` flag for special Diwali session
- **Additional channels** — engine dispatches via SignalRouter pattern; adding email/webhook is trivial
- **Strategy alerts** — morning report can include "strategies to watch today" based on market conditions
