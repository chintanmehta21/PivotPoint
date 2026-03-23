# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Dev Commands

```bash
pip install -e ".[dev]"          # Install with dev dependencies
cp .env.example .env             # Create env file, then fill in tokens

pytest                           # Run all tests (verbose, short traceback)
pytest tests/unit/               # Unit tests only
pytest tests/unit/test_models.py # Single test file
pytest -k "test_bullish"         # Run tests matching pattern
pytest --cov                     # With coverage (sources: src/quant, src/data_science, outputs)

ruff check src/ tests/ outputs/  # Lint
ruff format src/ tests/ outputs/ # Format
mypy src/                        # Type check (strict mode, tests exempt from untyped-defs)

pivotpoint info                  # Show registered strategies
pivotpoint scan                  # Run strategies (needs Fyers API)
pivotpoint serve                 # Start Discord/Telegram bots
```

## Architecture

Three sibling packages installed from one `pyproject.toml`:

- **`src/quant/`** — Core trading engine. CLI entry point: `quant.cli:cli`
- **`src/data_science/`** — ML/AI stubs (feature pipelines, sentiment analysis). Protocol-based, not yet implemented.
- **`outputs/`** — Signal delivery channels (Discord embeds, Telegram MarkdownV2, website dashboard). Each channel has a formatter (extends `BaseFormatter`) and a bot/writer.

### Signal Flow

```
Fyers API → MarketDataProvider (Protocol)
  → StrategyScanner (async, runs strategies via asyncio.to_thread)
    → 14 BaseStrategy subclasses (sync evaluate/build_position/check_exit/validate_entry)
      → RiskManager.pre_trade_check (max loss, VIX regime)
        → SignalRouter → Discord | Telegram | Database
```

### Strategy System

- `BaseStrategy` ABC in `src/quant/strategies/base_strategy.py` — all strategies implement `evaluate`, `build_position`, `check_exit`, `validate_entry`
- `StrategyRegistry` auto-discovers strategies by scanning `strategies/bullish/` and `strategies/bearish/` with `importlib`
- 6 bullish + 8 bearish strategies across WEEKLY/MONTHLY/QUARTERLY timeframes
- Each strategy has a `strategy_id` (e.g., BW1, BrM2) and targets NIFTY or BANKNIFTY

### Key Patterns

- **Pydantic everywhere**: all models (`SignalPayload`, `OptionsContract`, `MarketSnapshot`, `MultiLegPosition`) are Pydantic BaseModels; settings use `pydantic-settings` with `env_nested_delimiter="__"`
- **Protocol-based data layer**: `MarketDataProvider` is a `typing.Protocol`, not an ABC — primary implementation targets Fyers API
- **Structured logging**: `structlog` with JSON in production, console renderer locally. `APP_NAME` bound to all log context via `contextvars`
- **Decimal for money**: strikes, premiums, P&L use `Decimal`, never `float`
- **Custom exception hierarchy**: `PivotPointError` base in `quant/utils/exceptions.py` with domain-specific subtypes

## Commit Messages

- Use ONLY the message the user provides. If no message given, write a single-line commit message of 5-10 words explaining the major changes.
- NEVER include "Co-authored-by", "Co-Authored-By", or any attribution to Claude/AI in commit messages or trailers.

## Critical Conventions

- **APP_NAME is a single-point config** in `src/quant/config/identity.py` (overridable via `APP_NAME` env var). Never hardcode "PivotPoint" — always import from `quant.config.identity`
- **Fyers API** is the primary market data source. Credentials go in `secrets/` (gitignored). Use Context7 MCP for Fyers API docs.
- **Ruff** for linting+formatting (line length 120, Python 3.11 target). Rules: E, W, F, I, B, C4, UP, SIM. E501 ignored.
- **mypy strict** on `src/`, relaxed `disallow_untyped_defs` in `tests/`
- Test markers: `@pytest.mark.slow`, `@pytest.mark.integration`
- Shared test fixtures in `tests/conftest.py` (sample_contract, sample_market, sample_chain, sample_signal, etc.)
