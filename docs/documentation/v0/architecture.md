# PivotPoint Architecture

> **Note:** "PivotPoint" is configurable via `APP_NAME` in `src/pivotpoint/config/identity.py` or the `APP_NAME` environment variable. All outputs, logs, and interfaces reference this centralized identity.

## System Overview

```
Market Data (Fyers API)
       │
       ▼
┌─────────────────────┐
│   Strategy Scanner   │──── asyncio.to_thread() ────┐
└─────────────────────┘                               │
       │                                              ▼
       │                                    ┌──────────────────┐
       │                                    │  14 Strategies   │
       │                                    │  (sync evaluate) │
       │                                    └──────────────────┘
       ▼
┌─────────────────────┐
│   Risk Manager       │
│   (pre-trade checks) │
└─────────────────────┘
       │
       ▼
┌─────────────────────┐
│   Signal Router      │──── async dispatch ────┐
│   (async)            │                        │
└─────────────────────┘                        │
       │                    ┌──────────────────┤
       ▼                    ▼                  ▼
┌──────────┐      ┌──────────────┐    ┌──────────┐
│ Discord  │      │  Telegram    │    │ Database  │
│ (Embeds) │      │ (MarkdownV2) │    │(SQLAlchemy│
└──────────┘      └──────────────┘    └──────────┘
```

## Module Structure

```
src/pivotpoint/
├── config/          # Identity (APP_NAME), Settings (pydantic-settings)
├── models/          # Pydantic models: OptionsContract, SignalPayload, etc.
├── strategies/      # BaseStrategy ABC + 14 concrete strategies
│   ├── bullish/     # 6 bullish (BW1, BW2, BM1, BM2, BQ1, BQ2)
│   └── bearish/     # 8 bearish (BrW1-3, BrM1-3, BrQ1-2)
├── execution/       # SignalRouter, StrategyScanner, PositionSizer
├── risk/            # RiskManager, PositionTracker
├── data/            # MarketDataProvider Protocol, validators
├── outputs/         # Discord, Telegram, Database writers
├── data_science/    # ML/AI stubs for future integration
├── utils/           # Exceptions, types, logging, decorators
└── cli.py           # Click CLI entry point
```

## Key Design Decisions

### Async Architecture
- **Strategies are sync** — pure evaluation logic, no I/O
- **Bots and router are async** — network I/O for Discord/Telegram
- **Bridge:** `asyncio.to_thread()` wraps sync strategy calls in the async scanner

### Configuration
- `pydantic-settings` with nested `BaseModel` groups
- Environment variables use `__` delimiter: `DISCORD__BOT_TOKEN`
- Fail-fast validation at import time

### Data Flow
1. `MarketDataProvider` (Fyers API) provides `MarketSnapshot` + `OptionsChain`
2. `StrategyScanner` evaluates all registered strategies
3. `RiskManager` validates signals against portfolio limits
4. `SignalRouter` dispatches to all output channels concurrently
5. Each channel formats independently (Embed, MarkdownV2, SQL)

### Strategy Registration
- `importlib` auto-discovery scans `bullish/` and `bearish/` subdirectories
- Any `BaseStrategy` subclass with a `strategy_id` is automatically registered
- Adding a new strategy = drop a file in the correct directory

### Branding
- `APP_NAME` in `config/identity.py` is the single rename point
- Referenced in: Discord embeds, Telegram prefixes, DB table names, CLI, logs

## Adding a New Strategy

1. Create a file in `strategies/bullish/` or `strategies/bearish/`
2. Inherit from `BaseStrategy`
3. Define class attributes: `name`, `strategy_id`, `direction`, `timeframe`, `description`
4. Implement: `evaluate()`, `build_position()`, `check_exit()`, `validate_entry()`
5. Import it in the subpackage's `__init__.py`
6. It will be auto-discovered by `StrategyRegistry`

## Adding a New Output Channel

1. Create a module in `outputs/`
2. Implement the `OutputChannel` protocol: `async def send_signal(signal: SignalPayload) -> None`
3. Register with `SignalRouter.register_channel()`

## Future Integration Points

- **Fyers API**: Primary market data provider (Protocol stub in `data/provider.py`)
- **ML Models**: `data_science/ml/models/base_model.py` — `ModelInterface` Protocol
- **Feature Pipelines**: `data_science/ml/features/base_pipeline.py` — `FeaturePipeline` Protocol
- **News Sentiment**: `data_science/ai/news/sentiment_analyzer.py` — NLP/LLM integration
- **Order Execution**: `execution/order_manager.py` — broker integration Protocol
