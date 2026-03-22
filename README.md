# PivotPoint

Options trading signal generation system. Implements 14 options strategies (6 bullish, 8 bearish) across weekly, monthly, and quarterly timeframes for Indian markets (Nifty, Bank Nifty).

## Setup

```bash
pip install -e ".[dev]"
cp .env.example .env
# Edit .env with your API tokens
```

## Usage

```bash
pivotpoint info     # Show registered strategies
pivotpoint scan     # Run strategies against market data
pivotpoint serve    # Start alert bots
```

## Architecture

See `docs/v0/architecture.md` for full system design.
