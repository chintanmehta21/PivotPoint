# PivotPoint — Project Init Plan (v2)

## Overview
Scaffold and build a complete options trading system repository. 14 strategies across 6 categories (bullish/bearish x weekly/monthly/quarterly) from research outputs, with multi-channel alerting (Discord, Telegram), quant dashboard/DB, and AI/ML-ready architecture.

### Design Decisions (from plugin review)
| Decision | Choice | Source |
|----------|--------|--------|
| Project layout | `src/` layout — `src/pivotpoint/` is the package, `src/` is NOT a package | `python-packaging` |
| Package name | `pivotpoint` — configurable via `APP_NAME` in `src/pivotpoint/config/identity.py` | User requirement |
| Naming convention | `snake_case` everywhere — `data_science` not `dataScience` | `python-code-style` |
| Config management | `pydantic-settings` with nested `BaseModel` groups, fail-fast at import | `python-configuration` |
| Logging | `structlog` with JSON output, correlation IDs | `python-observability` |
| Type checking | `mypy --strict` via `pyproject.toml`, `py.typed` marker | `python-type-safety` |
| Linting/formatting | `ruff` (replaces black + isort + flake8) | `python-code-style` |
| Line length | 120 characters | `python-code-style` |
| Docstrings | Google-style | `python-code-style` |
| Interfaces | `Protocol` for external boundaries, `ABC` for strategy base | `python-type-safety` + `python-design-patterns` |
| Strategy registry | `importlib` auto-discovery of `BaseStrategy` subclasses | User requirement |
| Async boundary | Strategies = sync, Bots/Router = async, bridge via `asyncio.to_thread()` | `async-python-patterns` |
| Testing | `pytest` + `pytest-asyncio` + parameterized + coverage | `python-testing-patterns` |
| DB layer | SQLAlchemy (not raw sqlite3) | `python-design-patterns` (DI) |
| Discord output | `discord.Embed` objects (not plain strings) | Corrected from v1 |
| Public APIs | `__all__` in every `__init__.py` | `python-project-structure` |

---

## Strategy Inventory (from `/.init/strategies_v1/`)

### Bullish (6 strategies)
| ID | Name | Timeframe | Score | Legs | Key Feature |
|----|------|-----------|-------|------|-------------|
| BW1 | Call Ratio Backspread 1:2 | Weekly | 72 | 3 | Net credit, unlimited upside |
| BW2 | Supertrend Bull Call Spread | Weekly | 70 | 2 | Signal-driven, vega-neutral |
| BM1 | Modified Butterfly [MERGED] | Monthly | 78 | 4 | 4:1 R:R, short vega |
| BM2 | Bullish Diagonal Calendar [MERGED] | Monthly | 71 | 2+rolls | Triple-positive Greeks |
| BQ1 | Bullish-Adjusted Iron Fly | Quarterly | 76 | 6 (2-phase) | Neutral->bullish adjustment |
| BQ2 | Broken Wing Call Butterfly | Quarterly | 74 | 4 | Asymmetric payoff, cheap wing |

### Bearish (8 strategies)
| ID | Name | Timeframe | Score | Legs | Key Feature |
|----|------|-----------|-------|------|-------------|
| BrW1 | Bearish Diagonal/Calendar Put [MERGED] | Weekly | 82 | 2+rolls | Long vega, crisis hedge |
| BrW2 | Put Ratio Backspread | Weekly | 78 | 3 | Crash hedge, net credit |
| BrW3 | Bearish Broken-Wing Put Butterfly | Weekly | 73 | 4 | Skew harvest, pin strategy |
| BrM1 | Bearish Jade Lizard | Monthly | 80 | 3 | Zero upside risk |
| BrM2 | Bank Nifty Bear Call Credit Spread | Monthly | 75 | 2 | >75% POP, defined risk |
| BrM3 | Bearish Put Ladder | Monthly | 71 | 3 | Staircase support targets |
| BrQ1 | Skip-Strike Bearish Put Butterfly | Quarterly | 92 | 4 | No downside loss, guaranteed floor |
| BrQ2 | Bear Put Condor - Adaptive Bear | Quarterly | 87 | 4 | Absolute loss cap both sides |

---

## Phase 0: Project Bootstrap & Strategy Copy
**Goal:** Copy strategy files, initialize git, create pyproject.toml, install editable package.

### Tasks

0.1. **Initialize git repo:**
   ```bash
   cd PivotPoint && git init
   ```

0.2. **Copy strategy files** from `C:/Users/LENOVO/Documents/Claude_Code/MyAgents/agent_outputs/trading research/run_20032026/final/` to `.init/strategies_v1/`

0.3. **Create `pyproject.toml`** (full-featured, PEP 621):
   ```toml
   [build-system]
   requires = ["setuptools>=61.0", "wheel"]
   build-backend = "setuptools.build_meta"

   [project]
   name = "pivotpoint"
   version = "0.1.0"
   description = "Options trading signal generation system"
   requires-python = ">=3.12"
   dependencies = [
       "pydantic>=2.6.0,<3.0.0",
       "pydantic-settings>=2.2.0,<3.0.0",
       "structlog>=24.1.0",
       "discord.py>=2.3.0,<3.0.0",
       "python-telegram-bot>=21.0,<22.0",
       "sqlalchemy>=2.0.0,<3.0.0",
       "aiosqlite>=0.20.0",
       "pandas>=2.2.0,<3.0.0",
       "numpy>=1.26.0,<3.0.0",
       "httpx>=0.27.0,<1.0.0",
       "python-dotenv>=1.0.0",
       "jinja2>=3.1.0,<4.0.0",
   ]

   [project.optional-dependencies]
   dev = [
       "pytest>=8.0.0",
       "pytest-asyncio>=0.23.0",
       "pytest-cov>=5.0.0",
       "ruff>=0.3.0",
       "mypy>=1.8.0",
       "freezegun>=1.4.0",
   ]

   [project.scripts]
   pivotpoint = "pivotpoint.cli:cli"

   [tool.setuptools.packages.find]
   where = ["src"]

   [tool.ruff]
   line-length = 120
   target-version = "py312"

   [tool.ruff.lint]
   select = ["E", "W", "F", "I", "B", "C4", "UP", "SIM"]
   ignore = ["E501"]

   [tool.mypy]
   python_version = "3.12"
   strict = true
   warn_return_any = true
   warn_unused_ignores = true

   [[tool.mypy.overrides]]
   module = "tests.*"
   disallow_untyped_defs = false

   [tool.pytest.ini_options]
   testpaths = ["tests"]
   python_files = ["test_*.py"]
   addopts = "-v --tb=short --cov=pivotpoint --cov-report=term-missing"
   markers = [
       "slow: marks slow tests",
       "integration: marks integration tests",
   ]

   [tool.coverage.run]
   source = ["src/pivotpoint"]
   omit = ["*/tests/*"]

   [tool.coverage.report]
   exclude_lines = [
       "pragma: no cover",
       "raise NotImplementedError",
       "if TYPE_CHECKING:",
       "\\.\\.\\.",
   ]
   ```

0.4. **Create `.gitignore`** (Python + .env + IDE + build artifacts)

0.5. **Create `.env.example`** with all required variable names:
   ```bash
   # Identity (override system name)
   # APP_NAME=PivotPoint

   # Discord
   DISCORD__BOT_TOKEN=
   DISCORD__CHANNEL_ID=

   # Telegram
   TELEGRAM__BOT_TOKEN=
   TELEGRAM__CHAT_ID=

   # Database
   DATABASE__URL=sqlite+aiosqlite:///pivotpoint.db

   # Risk
   RISK__MAX_PORTFOLIO_LOSS=50000
   RISK__MAX_POSITIONS_PER_UNDERLYING=3
   RISK__VIX_HIGH_THRESHOLD=20.0
   RISK__VIX_LOW_THRESHOLD=14.0

   # Logging
   LOG_LEVEL=INFO
   ENVIRONMENT=local
   ```

0.6. **Install in editable mode:**
   ```bash
   pip install -e ".[dev]"
   ```

### Verification
- [ ] `pip install -e ".[dev]"` succeeds
- [ ] `python -c "import pivotpoint"` succeeds
- [ ] `.init/strategies_v1/` contains all 6 `.md` files
- [ ] Git repo initialized with initial commit

---

## Phase 1: Core Infrastructure — Identity, Config, Logging, Types, Exceptions
**Goal:** Create the foundational modules that everything else depends on.

### Tasks

1.1. **System identity** (`src/pivotpoint/config/identity.py`):
   ```python
   """Single source of truth for system identity.

   Change APP_NAME here to rebrand the entire system —
   all outputs, logs, bot names, DB tables, and docs reference this.
   """
   import os

   APP_NAME: str = os.environ.get("APP_NAME", "PivotPoint")
   APP_NAME_LOWER: str = APP_NAME.lower()
   APP_NAME_SNAKE: str = APP_NAME.lower().replace(" ", "_")
   APP_VERSION: str = "0.1.0"
   APP_DESCRIPTION: str = f"{APP_NAME} — Options Trading Signal System"
   ```

   **Usage everywhere:** `from pivotpoint.config.identity import APP_NAME`
   - Discord bot name: `f"{APP_NAME} Alerts"`
   - Telegram bot prefix: `f"[{APP_NAME}]"`
   - DB table prefix: `f"{APP_NAME_SNAKE}_signals"`
   - Log context: `structlog.contextvars.bind_contextvars(app=APP_NAME)`
   - Dashboard title: `f"{APP_NAME} Dashboard"`
   - README header: `f"# {APP_NAME}"`
   - Signal messages: `f"--- {APP_NAME} Signal ---"`

1.2. **Configuration** (`src/pivotpoint/config/settings.py`):
   - Single `Settings` class using `pydantic_settings.BaseSettings`
   - Nested config groups via `BaseModel`:
     ```python
     class DiscordSettings(BaseModel):
         bot_token: str = ""
         channel_id: str = ""

     class TelegramSettings(BaseModel):
         bot_token: str = ""
         chat_id: str = ""

     class DatabaseSettings(BaseModel):
         url: str = "sqlite+aiosqlite:///pivotpoint.db"

     class RiskSettings(BaseModel):
         max_portfolio_loss: Decimal = Decimal("50000")
         max_positions_per_underlying: int = 3
         vix_high_threshold: float = 20.0
         vix_low_threshold: float = 14.0

     class Settings(BaseSettings):
         discord: DiscordSettings = DiscordSettings()
         telegram: TelegramSettings = TelegramSettings()
         database: DatabaseSettings = DatabaseSettings()
         risk: RiskSettings = RiskSettings()
         log_level: str = "INFO"
         environment: str = "local"

         model_config = SettingsConfigDict(
             env_nested_delimiter="__",
             env_file=".env",
             env_file_encoding="utf-8",
         )
     ```
   - Singleton at module level: `settings = Settings()`
   - Fail fast with clear error on validation failure
   - **No separate `secrets.py`** — secrets are fields on Settings with no defaults when required

1.3. **Config `__init__.py`** (`src/pivotpoint/config/__init__.py`):
   ```python
   from .identity import APP_NAME, APP_VERSION, APP_DESCRIPTION
   from .settings import Settings, settings

   __all__ = ["APP_NAME", "APP_VERSION", "APP_DESCRIPTION", "Settings", "settings"]
   ```

1.4. **Structured logging** (`src/pivotpoint/utils/logger.py`):
   - Uses `structlog` (not stdlib `logging`)
   - JSON output in production, human-readable in local dev
   - Binds `APP_NAME` to all log entries via contextvars
   - `configure_logging(log_level: str, environment: str) -> None`
   - Called once at app startup

1.5. **Exceptions** (`src/pivotpoint/utils/exceptions.py`):
   - Base: `PivotPointError(Exception)` — all custom exceptions inherit from this
   - Domain exceptions with structured context:
     ```python
     class ContractExpiredError(PivotPointError):
         def __init__(self, symbol: str, expiry: date) -> None:
             self.symbol = symbol
             self.expiry = expiry
             super().__init__(f"Contract expired: {symbol} @ {expiry}")
     ```
   - Full list: `ContractExpiredError`, `MissingGreeksError`, `IlliquidStrikeError`, `MarketClosedError`, `InsufficientDataError`, `ConfigurationError`, `SignalValidationError`, `StrategyEvaluationError`
   - All carry structured context fields (not just message strings)

1.6. **Enums & type aliases** (`src/pivotpoint/utils/types.py`):
   - `OptionType(str, Enum)`: `CE`, `PE`
   - `Direction(str, Enum)`: `BULLISH`, `BEARISH`
   - `TimeFrame(str, Enum)`: `WEEKLY`, `MONTHLY`, `QUARTERLY`
   - `SignalType(str, Enum)`: `ENTRY`, `EXIT`, `ADJUSTMENT`
   - `Side(str, Enum)`: `BUY`, `SELL`
   - `Underlying(str, Enum)`: `NIFTY`, `BANKNIFTY`
   - Type aliases: `Strike = Decimal`, `Premium = Decimal`

1.7. **Data models** (`src/pivotpoint/models/`):
   - **Moved from `data/models.py`** — models are a top-level concern, not under `data/`
   - `__init__.py` with `__all__` exporting all public models
   - `contracts.py` — Pydantic models:
     - `OptionsContract` — symbol, expiry, strike, option_type (CE/PE), premium, lot_size
     - `GreeksSnapshot` — delta, gamma, vega, theta, iv
     - `PositionLeg` — contract + quantity + side (BUY/SELL)
     - `MultiLegPosition` — list of PositionLeg with computed properties:
       - `net_premium -> Decimal`
       - `max_profit -> Decimal | None`
       - `max_loss -> Decimal | None`
       - `is_credit -> bool`
   - `market.py`:
     - `MarketSnapshot` — underlying, price, timestamp, vix_level
     - `OptionsChain` — underlying, expiry, contracts list
   - `signals.py`:
     - `SignalPayload` (Pydantic BaseModel, NOT in `utils/`):
       ```python
       class SignalPayload(BaseModel):
           timestamp: datetime
           strategy_name: str
           strategy_id: str
           underlying: Underlying
           timeframe: TimeFrame
           direction: Direction
           position: MultiLegPosition
           max_profit: Decimal
           max_loss: Decimal
           risk_reward_ratio: float
           confidence_score: float  # 0-100
           greeks: GreeksSnapshot
           signal_type: SignalType
           notes: str = ""
       ```

1.8. **Market data provider** (`src/pivotpoint/data/provider.py`):
   - `MarketDataProvider(Protocol)` — structural interface (not ABC):
     ```python
     class MarketDataProvider(Protocol):
         async def get_options_chain(self, underlying: Underlying, expiry: date) -> OptionsChain: ...
         async def get_market_snapshot(self, underlying: Underlying) -> MarketSnapshot: ...
     ```
   - No implementation yet — just the protocol
   - `data/validators.py` — business logic validation (expiry not past, strike reasonable, lot size correct)

1.9. **Package `__init__.py`** (`src/pivotpoint/__init__.py`):
   ```python
   """PivotPoint — Options Trading Signal System."""
   from pivotpoint.config.identity import APP_NAME, APP_VERSION
   __all__ = ["APP_NAME", "APP_VERSION"]
   __version__ = APP_VERSION
   ```

1.10. **`py.typed`** marker file at `src/pivotpoint/py.typed` (empty file for PEP 561)

### Verification
- [ ] `python -c "from pivotpoint.config import APP_NAME, settings; print(APP_NAME)"` prints `PivotPoint`
- [ ] `python -c "from pivotpoint.models import SignalPayload, OptionsContract"` succeeds
- [ ] `APP_NAME=CustomName python -c "from pivotpoint.config import APP_NAME; print(APP_NAME)"` prints `CustomName`
- [ ] Missing required env vars (when no defaults) raise `ValidationError` at import
- [ ] `ruff check src/` passes
- [ ] `mypy src/pivotpoint/config/ src/pivotpoint/utils/ src/pivotpoint/models/` passes

---

## Phase 2A: Strategy Framework — Base & Bullish (6 strategies)
**Goal:** Build abstract strategy base, implement 6 bullish strategies, start the registry.

### Tasks

2A.1. **Abstract base** (`src/pivotpoint/strategies/base_strategy.py`):
   - `BaseStrategy(ABC)`:
     - Class attributes: `name: str`, `strategy_id: str`, `direction: Direction`, `timeframe: TimeFrame`, `description: str`
     - Abstract methods:
       - `evaluate(market: MarketSnapshot, chain: OptionsChain) -> SignalPayload | None`
       - `build_position(chain: OptionsChain, market: MarketSnapshot) -> MultiLegPosition`
       - `check_exit(position: MultiLegPosition, market: MarketSnapshot) -> SignalPayload | None`
       - `validate_entry(market: MarketSnapshot) -> bool`
     - Concrete methods:
       - `calculate_position_greeks(position: MultiLegPosition) -> GreeksSnapshot`
       - `_create_signal(position: MultiLegPosition, market: MarketSnapshot, signal_type: SignalType, notes: str = "") -> SignalPayload`
       - `__repr__() -> str` — uses `APP_NAME` in repr

2A.2. **Bullish strategies** (`src/pivotpoint/strategies/bullish/`):
   - `__init__.py` with `__all__`
   - Each strategy file: full class with `# TODO:` for logic that needs live market data
   - `call_ratio_backspread.py` — BW1
   - `supertrend_bull_call_spread.py` — BW2
   - `modified_butterfly.py` — BM1
   - `bullish_diagonal_calendar.py` — BM2
   - `bullish_adjusted_iron_fly.py` — BQ1
   - `broken_wing_call_butterfly.py` — BQ2

2A.3. **Strategy registry** (`src/pivotpoint/strategies/registry.py`):
   - `StrategyRegistry`:
     - `__init__()` — calls `_auto_discover()` on instantiation
     - `_auto_discover()` — uses `importlib` + `pkgutil` to scan `bullish/` and `bearish/` subpackages, finds all `BaseStrategy` subclasses
     - `get(strategy_id: str) -> BaseStrategy`
     - `by_direction(direction: Direction) -> list[BaseStrategy]`
     - `by_timeframe(timeframe: TimeFrame) -> list[BaseStrategy]`
     - `all() -> dict[str, BaseStrategy]`
     - `count -> int`

### Verification
- [ ] `from pivotpoint.strategies.base_strategy import BaseStrategy` succeeds
- [ ] Instantiating `BaseStrategy` directly raises `TypeError`
- [ ] Each bullish strategy class instantiates without error
- [ ] `StrategyRegistry().count` returns `6` (bearish not yet implemented)
- [ ] Each strategy's `name`, `direction`, `timeframe` properties return correct values

---

## Phase 2B: Strategy Framework — Bearish (8 strategies)
**Goal:** Implement all 8 bearish strategies.

### Tasks

2B.1. **Bearish strategies** (`src/pivotpoint/strategies/bearish/`):
   - `__init__.py` with `__all__`
   - `bearish_diagonal_calendar_put.py` — BrW1 (Score: 82, highest weekly)
   - `put_ratio_backspread.py` — BrW2 (Score: 78, crash hedge)
   - `bearish_broken_wing_put_butterfly.py` — BrW3 (Score: 73, pin strategy)
   - `bearish_jade_lizard.py` — BrM1 (Score: 80, zero upside risk)
   - `bear_call_credit_spread.py` — BrM2 (Score: 75, Bank Nifty)
   - `bearish_put_ladder.py` — BrM3 (Score: 71, staircase)
   - `skip_strike_bearish_put_butterfly.py` — BrQ1 (Score: 92, BEST in pipeline)
   - `bear_put_condor.py` — BrQ2 (Score: 87, absolute cap)

### Verification
- [ ] `StrategyRegistry().count` returns `14`
- [ ] `len(StrategyRegistry().by_direction(Direction.BEARISH))` returns `8`
- [ ] `len(StrategyRegistry().by_direction(Direction.BULLISH))` returns `6`
- [ ] All strategies importable individually

---

## Phase 3: Execution & Risk Layer
**Goal:** Build signal routing (async), position sizing, risk management, and the strategy scanner.

### Tasks

3.1. **Execution layer** (`src/pivotpoint/execution/`):
   - `__init__.py` with `__all__`
   - `signal_router.py` — `SignalRouter`:
     - **Async** — dispatches to async output channels concurrently
     - `async def dispatch(signal: SignalPayload) -> None`
     - Error isolation: one channel failure doesn't block others
     - Uses `asyncio.gather(*tasks, return_exceptions=True)` (batch failure pattern from plugin)
     - Logs dispatch results via structlog with signal context
   - `position_sizer.py` — `PositionSizer`:
     - Fixed fractional sizing (NOT Kelly — no historical data yet)
     - `calculate_lots(capital: Decimal, risk_per_trade: Decimal, max_loss: Decimal) -> int`
     - Respects lot sizes: Nifty=65, BankNifty=30
     - Configurable via `Settings.risk`
   - `order_manager.py` — `OrderManager(Protocol)`:
     - Structural interface (Protocol, not ABC) — broker-agnostic
     - Methods stubbed: `place_order`, `cancel_order`, `get_status`
     - `# FUTURE: Broker integration point`
   - `scanner.py` — `StrategyScanner`:
     - `async def scan(market: MarketSnapshot, chain: OptionsChain) -> list[SignalPayload]`
     - Iterates all registered strategies
     - Calls sync `evaluate()` via `asyncio.to_thread()` (sync-async bridge)
     - Passes through risk manager before collecting
     - Returns `BatchResult[SignalPayload]` (successes + failures tracked separately)

3.2. **Risk management** (`src/pivotpoint/risk/`):
   - `__init__.py` with `__all__`
   - `risk_manager.py` — `RiskManager`:
     - `pre_trade_check(signal: SignalPayload) -> bool` — returns True if signal passes all checks
     - Checks: max portfolio loss, max positions per underlying, VIX regime, market hours
     - Each check is a separate private method (testable individually)
     - Raises specific exceptions with context (not generic booleans)
   - `position_tracker.py` — `PositionTracker`:
     - In-memory tracking of open positions
     - `add_position(signal: SignalPayload) -> None`
     - `close_position(strategy_id: str, pnl: Decimal) -> None`
     - `portfolio_greeks -> GreeksSnapshot` (aggregated)
     - `portfolio_pnl -> Decimal`
   - `limits.py` — `RiskLimits` dataclass loaded from `settings.risk`

### Verification
- [ ] `SignalRouter` dispatches to mock channels without error
- [ ] `RiskManager.pre_trade_check()` rejects signals exceeding limits
- [ ] `PositionSizer.calculate_lots()` respects lot size constraints
- [ ] `StrategyScanner.scan()` returns `BatchResult` with partial failure handling
- [ ] Async tests pass with `pytest-asyncio`

---

## Phase 4: Output Channels
**Goal:** Build Discord bot, Telegram bot, and database writer. All inside `src/pivotpoint/outputs/`.

### Tasks

4.1. **Base formatter** (`src/pivotpoint/outputs/base_formatter.py`):
   - `BaseFormatter(ABC)`:
     - `format_entry(signal: SignalPayload) -> Any`
     - `format_exit(signal: SignalPayload) -> Any`
     - `format_adjustment(signal: SignalPayload) -> Any`
   - All formatters reference `APP_NAME` from identity for branding

4.2. **Discord** (`src/pivotpoint/outputs/discord/`):
   - `__init__.py` with `__all__`
   - `formatter.py` — `DiscordFormatter(BaseFormatter)`:
     - Returns `discord.Embed` objects (NOT plain strings)
     - `format_entry(signal) -> discord.Embed`:
       - Title: `f"[{APP_NAME}] {signal.direction.value} Signal"`
       - Color: green for bullish, red for bearish
       - Fields: strategy name, underlying, R:R, score, Greeks table
       - Footer: `f"{APP_NAME} v{APP_VERSION}"`
     - Similar for exit, adjustment
   - `bot.py` — `DiscordAlertBot`:
     - `async def send_signal(signal: SignalPayload) -> None`
     - Connects using `settings.discord.bot_token`
     - Posts embeds to `settings.discord.channel_id`
     - Webhook fallback if bot token not configured
   - `templates/` — Jinja2 templates for markdown fallback:
     - `entry_signal.j2`
     - `exit_signal.j2`
     - `daily_summary.j2`

4.3. **Telegram** (`src/pivotpoint/outputs/telegram/`):
   - `__init__.py` with `__all__`
   - `formatter.py` — `TelegramFormatter(BaseFormatter)`:
     - Returns MarkdownV2 strings
     - Prefixes all messages with `f"[{APP_NAME}]"`
   - `bot.py` — `TelegramAlertBot`:
     - `async def send_signal(signal: SignalPayload) -> None`
     - Uses `settings.telegram.bot_token`
     - Posts to `settings.telegram.chat_id`
     - Parse mode: MarkdownV2
   - `templates/` — Jinja2 templates:
     - `entry_signal.j2`
     - `exit_signal.j2`
     - `daily_summary.j2`

4.4. **Database** (`src/pivotpoint/outputs/database/`):
   - `__init__.py` with `__all__`
   - `schema.py` — SQLAlchemy ORM models (NOT raw SQL):
     - `SignalRecord` — maps from `SignalPayload`, table: `{APP_NAME_SNAKE}_signals`
     - `TradeRecord` — signal_id FK, execution_time, fill_price, status, actual_pnl
     - `StrategyPerformance` — strategy_id, total_trades, wins, losses, avg_rr, total_pnl
     - `MarketSnapshotRecord` — underlying, price, vix, timestamp
   - `writer.py` — `DatabaseWriter`:
     - `async def write_signal(signal: SignalPayload) -> int`
     - `async def update_trade(signal_id: int, status: str, pnl: Decimal) -> None`
     - `async def get_performance(strategy_id: str) -> dict`
     - Uses async SQLAlchemy with `aiosqlite`
   - `dashboard/` — stub for quant dashboard:
     - `__init__.py`
     - `data_provider.py` — async queries for dashboard consumption (stubbed)

### Verification
- [ ] `DiscordFormatter.format_entry(sample)` returns a `discord.Embed` with correct color and fields
- [ ] `TelegramFormatter.format_entry(sample)` returns valid MarkdownV2 string
- [ ] Both formatters include `APP_NAME` in their output
- [ ] DB schema creates tables with `APP_NAME_SNAKE` prefix
- [ ] `DatabaseWriter.write_signal()` inserts and returns signal_id
- [ ] Jinja2 templates render without errors

---

## Phase 5: Data Science / AI-ML Stubs
**Goal:** Create AI/ML-ready interfaces and stub classes. All under `src/pivotpoint/data_science/`.

### Tasks

5.1. **ML layer** (`src/pivotpoint/data_science/ml/`):
   - `__init__.py` with `__all__`
   - `features/`
     - `base_pipeline.py` — `FeaturePipeline(Protocol)` (Protocol, not ABC):
       - `def extract(market: MarketSnapshot, chain: OptionsChain) -> pd.DataFrame`
       - `def transform(features: pd.DataFrame) -> pd.DataFrame`
       - `# FUTURE: ML feature engineering integration point`
     - `iv_features.py` — stub
     - `greeks_features.py` — stub
   - `models/`
     - `base_model.py` — `ModelInterface(Protocol)`:
       - `def predict(features: pd.DataFrame) -> dict[str, float]`
       - `def train(data: pd.DataFrame) -> None`
       - `# FUTURE: ML model integration point`
   - `notebooks/` — `.gitkeep`
   - `configs/pipeline_config.py` — stub

5.2. **AI layer** (`src/pivotpoint/data_science/ai/`):
   - `news/sentiment_analyzer.py` — `NewsSentimentAnalyzer(Protocol)`:
     - `def analyze(headlines: list[str]) -> SentimentResult`
     - `# FUTURE: NLP/LLM integration for news-driven signals`

### Verification
- [ ] `from pivotpoint.data_science.ml.features.base_pipeline import FeaturePipeline` succeeds
- [ ] `from pivotpoint.data_science.ml.models.base_model import ModelInterface` succeeds
- [ ] All `__init__.py` files present with `__all__`

---

## Phase 6: CLI Entry Point & Main Runner
**Goal:** Create a CLI so the system can actually be run.

### Tasks

6.1. **CLI** (`src/pivotpoint/cli.py`):
   - Uses `click` (in dependencies)
   - Add `click>=8.1.0` to pyproject.toml dependencies
   ```python
   @click.group()
   @click.version_option(version=APP_VERSION, prog_name=APP_NAME)
   def cli():
       """Options trading signal system."""
       configure_logging(settings.log_level, settings.environment)

   @cli.command()
   def scan():
       """Run all strategies against current market data."""
       # TODO: requires MarketDataProvider implementation
       click.echo(f"[{APP_NAME}] Scanning {StrategyRegistry().count} strategies...")

   @cli.command()
   def serve():
       """Start alert bots (Discord + Telegram)."""
       click.echo(f"[{APP_NAME}] Starting alert services...")
       asyncio.run(_serve())

   @cli.command()
   def info():
       """Show system info and registered strategies."""
       registry = StrategyRegistry()
       click.echo(f"{APP_NAME} v{APP_VERSION}")
       click.echo(f"Strategies: {registry.count}")
       for sid, strategy in registry.all().items():
           click.echo(f"  {strategy.direction.value}/{strategy.timeframe.value}: {strategy.name}")
   ```

### Verification
- [ ] `pivotpoint --version` prints `PivotPoint 0.1.0`
- [ ] `pivotpoint info` lists all 14 strategies
- [ ] `pivotpoint scan` prints scanning message
- [ ] `APP_NAME=CustomBot pivotpoint --version` prints `CustomBot 0.1.0`

---

## Phase 7: Testing Framework
**Goal:** Full test infrastructure with fixtures, parameterized tests, async tests.

### Tasks

7.1. **Test setup:**
   - `tests/__init__.py`
   - `tests/conftest.py` — shared fixtures using `yield`:
     ```python
     @pytest.fixture
     def sample_contract() -> OptionsContract: ...

     @pytest.fixture
     def sample_market() -> MarketSnapshot: ...

     @pytest.fixture
     def sample_chain(sample_contract) -> OptionsChain: ...

     @pytest.fixture
     def sample_signal(sample_market) -> SignalPayload: ...

     @pytest.fixture
     def mock_settings(monkeypatch) -> Settings:
         """Settings with test defaults, no .env required."""
         monkeypatch.setenv("DISCORD__BOT_TOKEN", "test-token")
         ...
     ```

7.2. **Unit tests** (`tests/unit/`):
   - `test_identity.py` — test `APP_NAME` override via env var
   - `test_config.py` — test settings loading, nested env vars, missing var detection (monkeypatch)
   - `test_models.py` — test `OptionsContract`, `SignalPayload`, `GreeksSnapshot` creation/validation
   - `test_exceptions.py` — test all custom exceptions carry structured context
   - `test_types.py` — test enum values
   - Strategy tests — **parameterized** (one test class, many strategies):
     ```python
     @pytest.mark.parametrize("strategy_cls", [
         CallRatioBackspread,
         SupertrendBullCallSpread,
         ...all 14...
     ])
     def test_strategy_has_required_attributes(strategy_cls):
         s = strategy_cls()
         assert s.name
         assert s.direction in Direction
         assert s.timeframe in TimeFrame
     ```
   - Per-strategy tests for unique logic (one file per strategy, only for non-trivial logic):
     - `test_skip_strike_butterfly.py` — guaranteed profit floor validation
     - `test_jade_lizard.py` — zero upside risk property
     - etc. (not all 14 need individual files if parameterized covers basics)
   - `test_strategy_registry.py` — auto-discovery, lookup, filtering
   - `test_discord_formatter.py` — verify Embed fields, colors, `APP_NAME` presence
   - `test_telegram_formatter.py` — verify MarkdownV2 format, `APP_NAME` prefix
   - `test_db_writer.py` — in-memory SQLite, write/read cycle
   - `test_risk_manager.py` — rejection scenarios
   - `test_position_sizer.py` — lot size constraints

7.3. **Integration tests** (`tests/integration/`):
   - `test_signal_pipeline.py` — strategy -> signal -> formatter -> output (mock channels)
   - `test_risk_checks.py` — risk manager with realistic Nifty scenarios
   - `test_scanner.py` — `StrategyScanner` with mock market data (async)

### Verification
- [ ] `pytest tests/ --collect-only` discovers all test files
- [ ] `pytest tests/unit/test_models.py` passes
- [ ] `pytest tests/unit/test_strategy_registry.py` passes
- [ ] `pytest tests/unit/test_identity.py` passes (APP_NAME override works)
- [ ] `pytest --cov=pivotpoint` shows coverage report

---

## Phase 8: Documentation
**Goal:** Create architecture docs and strategy guide.

### Tasks

8.1. **Architecture doc** (`docs/v0/architecture.md`):
   - System overview (references `APP_NAME` as configurable)
   - Module dependency graph
   - Data flow: Market Data -> Strategy Evaluation -> Signal Generation -> Output Channels
   - Async architecture: sync strategies, async router/bots, `asyncio.to_thread()` bridge
   - Config management (pydantic-settings, nested groups)
   - How to add a new strategy (drop file in bullish/ or bearish/, inherit BaseStrategy)
   - How to add a new output channel

8.2. **Strategy guide** (`docs/v0/strategy_guide.md`):
   - Summary table of all 14 strategies (from inventory above)
   - Classification by direction, timeframe, risk profile
   - Greeks profiles comparison
   - Correlation matrix notes (from research files)
   - IV regime suitability matrix
   - How to add a new strategy (inherit `BaseStrategy`, place in correct dir)

### Verification
- [ ] Both docs exist and reference `APP_NAME` as configurable
- [ ] Strategy guide covers all 14 strategies
- [ ] Architecture doc matches actual code structure

---

## Phase 9: Final Verification
**Goal:** Ensure everything works together. Lint, type-check, test.

### Tasks

9.1. **Import verification:**
   ```bash
   python -c "
   from pivotpoint.config import APP_NAME, settings
   from pivotpoint.strategies.registry import StrategyRegistry
   from pivotpoint.models import SignalPayload, OptionsContract
   from pivotpoint.execution.signal_router import SignalRouter
   from pivotpoint.risk.risk_manager import RiskManager
   from pivotpoint.outputs.discord.formatter import DiscordFormatter
   from pivotpoint.outputs.telegram.formatter import TelegramFormatter
   from pivotpoint.outputs.database.writer import DatabaseWriter
   print(f'{APP_NAME} - All imports OK')
   r = StrategyRegistry()
   print(f'Registered strategies: {r.count}')
   for sid, s in r.all().items():
       print(f'  {s.direction.value}/{s.timeframe.value}: {s.name}')
   "
   ```

9.2. **Quality gates:**
   ```bash
   ruff check src/ tests/
   ruff format --check src/ tests/
   mypy src/pivotpoint/
   pytest tests/ -v --cov=pivotpoint --cov-fail-under=60
   ```

9.3. **Structure checks:**
   - Grep for `print(` in `src/` — should find zero (structlog only)
   - Grep for hardcoded API keys/tokens — should find zero
   - Grep for `APP_NAME` usage — should appear in outputs, CLI, logger, docs
   - Verify all `__init__.py` have `__all__`
   - Verify `.env.example` lists all env vars referenced in Settings

9.4. **Final checklist:**
   - [ ] 14 strategy classes, all inheriting `BaseStrategy`
   - [ ] Registry auto-discovers all 14 via importlib
   - [ ] `APP_NAME` referenced in: Discord embeds, Telegram messages, DB table names, CLI output, log context, README
   - [ ] `APP_NAME=X` override propagates everywhere
   - [ ] `SignalPayload` used by all output channels
   - [ ] All exceptions carry structured context
   - [ ] `structlog` used everywhere (no `print()`, no stdlib `logging`)
   - [ ] No hardcoded secrets
   - [ ] All public methods have type annotations
   - [ ] All modules have Google-style docstrings
   - [ ] `__all__` in every `__init__.py`
   - [ ] `py.typed` marker exists
   - [ ] `ruff check` clean
   - [ ] `mypy --strict` clean
   - [ ] Tests pass with >60% coverage
   - [ ] `.init/strategies_v1/` contains all 6 source files
   - [ ] `pivotpoint info` lists all 14 strategies
   - [ ] `pivotpoint --version` shows correct name and version

---

## File Manifest (Complete)

```
PivotPoint/
├── .init/
│   └── strategies_v1/
│       ├── top3_bullish_weekly.md
│       ├── top3_bullish_monthly.md
│       ├── top3_bullish_quarterly.md
│       ├── top3_bearish_weekly.md
│       ├── top3_bearish_monthly.md
│       └── top3_bearish_quarterly.md
├── src/
│   └── pivotpoint/
│       ├── __init__.py              # APP_NAME, __version__
│       ├── py.typed                 # PEP 561 marker
│       ├── cli.py                   # Click CLI entry point
│       ├── config/
│       │   ├── __init__.py          # exports APP_NAME, settings
│       │   ├── identity.py          # APP_NAME, APP_VERSION (single source of truth)
│       │   └── settings.py          # pydantic-settings with nested groups
│       ├── models/
│       │   ├── __init__.py          # exports all models
│       │   ├── contracts.py         # OptionsContract, GreeksSnapshot, MultiLegPosition
│       │   ├── market.py            # MarketSnapshot, OptionsChain
│       │   └── signals.py           # SignalPayload
│       ├── strategies/
│       │   ├── __init__.py
│       │   ├── base_strategy.py     # BaseStrategy(ABC)
│       │   ├── registry.py          # StrategyRegistry (importlib auto-discover)
│       │   ├── bullish/
│       │   │   ├── __init__.py
│       │   │   ├── call_ratio_backspread.py
│       │   │   ├── supertrend_bull_call_spread.py
│       │   │   ├── modified_butterfly.py
│       │   │   ├── bullish_diagonal_calendar.py
│       │   │   ├── bullish_adjusted_iron_fly.py
│       │   │   └── broken_wing_call_butterfly.py
│       │   └── bearish/
│       │       ├── __init__.py
│       │       ├── bearish_diagonal_calendar_put.py
│       │       ├── put_ratio_backspread.py
│       │       ├── bearish_broken_wing_put_butterfly.py
│       │       ├── bearish_jade_lizard.py
│       │       ├── bear_call_credit_spread.py
│       │       ├── bearish_put_ladder.py
│       │       ├── skip_strike_bearish_put_butterfly.py
│       │       └── bear_put_condor.py
│       ├── execution/
│       │   ├── __init__.py
│       │   ├── signal_router.py     # Async dispatch to all channels
│       │   ├── position_sizer.py    # Fixed fractional sizing
│       │   ├── order_manager.py     # Protocol stub (broker-agnostic)
│       │   └── scanner.py           # Async scanner with BatchResult
│       ├── risk/
│       │   ├── __init__.py
│       │   ├── risk_manager.py
│       │   ├── position_tracker.py
│       │   └── limits.py
│       ├── data/
│       │   ├── __init__.py
│       │   ├── provider.py          # MarketDataProvider(Protocol)
│       │   └── validators.py        # Business logic validation
│       ├── outputs/
│       │   ├── __init__.py
│       │   ├── base_formatter.py    # BaseFormatter(ABC)
│       │   ├── discord/
│       │   │   ├── __init__.py
│       │   │   ├── formatter.py     # Returns discord.Embed
│       │   │   ├── bot.py           # Async Discord bot
│       │   │   └── templates/
│       │   │       ├── entry_signal.j2
│       │   │       ├── exit_signal.j2
│       │   │       └── daily_summary.j2
│       │   ├── telegram/
│       │   │   ├── __init__.py
│       │   │   ├── formatter.py     # Returns MarkdownV2
│       │   │   ├── bot.py           # Async Telegram bot
│       │   │   └── templates/
│       │   │       ├── entry_signal.j2
│       │   │       ├── exit_signal.j2
│       │   │       └── daily_summary.j2
│       │   └── database/
│       │       ├── __init__.py
│       │       ├── schema.py        # SQLAlchemy ORM models
│       │       ├── writer.py        # Async DatabaseWriter
│       │       └── dashboard/
│       │           ├── __init__.py
│       │           └── data_provider.py
│       ├── data_science/
│       │   ├── __init__.py
│       │   ├── ml/
│       │   │   ├── __init__.py
│       │   │   ├── features/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── base_pipeline.py   # FeaturePipeline(Protocol)
│       │   │   │   ├── iv_features.py
│       │   │   │   └── greeks_features.py
│       │   │   ├── models/
│       │   │   │   ├── __init__.py
│       │   │   │   └── base_model.py      # ModelInterface(Protocol)
│       │   │   ├── notebooks/
│       │   │   │   └── .gitkeep
│       │   │   └── configs/
│       │   │       ├── __init__.py
│       │   │       └── pipeline_config.py
│       │   └── ai/
│       │       ├── __init__.py
│       │       └── news/
│       │           ├── __init__.py
│       │           └── sentiment_analyzer.py
│       └── utils/
│           ├── __init__.py
│           ├── logger.py            # structlog config
│           ├── exceptions.py        # PivotPointError hierarchy
│           ├── decorators.py        # timing, retry
│           └── types.py             # Enums, type aliases
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # Shared fixtures
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_identity.py
│   │   ├── test_config.py
│   │   ├── test_models.py
│   │   ├── test_exceptions.py
│   │   ├── test_types.py
│   │   ├── test_strategies_parametrized.py  # All 14 via parametrize
│   │   ├── test_skip_strike_butterfly.py    # Unique logic
│   │   ├── test_jade_lizard.py              # Unique logic
│   │   ├── test_strategy_registry.py
│   │   ├── test_discord_formatter.py
│   │   ├── test_telegram_formatter.py
│   │   ├── test_db_writer.py
│   │   ├── test_risk_manager.py
│   │   └── test_position_sizer.py
│   └── integration/
│       ├── __init__.py
│       ├── test_signal_pipeline.py
│       ├── test_risk_checks.py
│       └── test_scanner.py
├── docs/
│   └── v0/
│       ├── architecture.md
│       └── strategy_guide.md
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

**Total files: ~90**

---

## Execution Notes

- **Phase dependencies:** 0 -> 1 -> 2A -> 2B -> 3 -> 4,5 (parallel) -> 6 -> 7 -> 8 -> 9
- **Parallelizable:** Phase 4 (outputs) and Phase 5 (data_science stubs) can run in parallel
- **Phase 2 split:** 2A (base + 6 bullish) and 2B (8 bearish) can be separate sessions
- **Strategy source path:** `C:/Users/LENOVO/Documents/Claude_Code/MyAgents/agent_outputs/trading research/run_20032026/final/` (note: space in "trading research")
- **Each phase is self-contained** — can be executed in a new chat context with this plan
- **No broker integration** — order execution is a Protocol stub. Market data provider is a Protocol. This is a signal generation system.
- **All imports use `pivotpoint.`** prefix — `pip install -e .` makes this work via src layout
- **`APP_NAME` is the single rename point** — change it in `identity.py` or via `APP_NAME` env var and everything updates

## Changes from v1
| Area | v1 | v2 (improved) |
|------|-----|----------------|
| Package name | `src/quant/` | `src/pivotpoint/` (src layout, no `src/__init__.py`) |
| Branding | Hardcoded everywhere | `APP_NAME` in `identity.py`, referenced everywhere |
| Config | `settings.py` + `secrets.py` | Single `Settings(BaseSettings)` with nested groups |
| Logging | stdlib `logging` | `structlog` with JSON + correlation IDs |
| Types | No `__all__`, no `py.typed` | `__all__` everywhere, `py.typed` marker |
| Linting | Not specified | `ruff` + `mypy --strict` in pyproject.toml |
| Interfaces | ABC everywhere | `Protocol` for external boundaries, `ABC` for strategies |
| Async | Unspecified | Clear boundary: sync strategies, async bots/router |
| Discord | Returns `str` | Returns `discord.Embed` |
| Templates | `.txt` files | Jinja2 `.j2` templates |
| Testing | 14 separate test files | Parameterized + targeted individual tests |
| `dataScience` | camelCase | `data_science` (snake_case) |
| `outputs/` | Separate top-level dir | Inside `src/pivotpoint/outputs/` |
| `signal_payload` | In `utils/` | In `models/signals.py` |
| DB | "SQLAlchemy or sqlite3" | SQLAlchemy ORM + aiosqlite (decided) |
| Position sizing | Kelly criterion | Fixed fractional (Kelly needs backtest data) |
| Entry point | None | `click` CLI: `pivotpoint scan/serve/info` |
| Phase 2 | One massive phase (14 strategies) | Split into 2A (bullish) + 2B (bearish) |
| `validators.py` | Overlapped Pydantic | Business logic only (not field validation) |
| Strategy registry | `strategy_registry.py` | `registry.py` (shorter name) |
