"""Market data provider interface (Protocol)."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Protocol

import pandas as pd

from quant.models.contracts import GreeksSnapshot
from quant.models.market import MarketSnapshot, OptionsChain
from quant.utils.types import Underlying


class MarketDataProvider(Protocol):
    """Protocol for market data providers. Primary implementation: Fyers API."""

    async def initialize(self) -> None:
        """Initialize the provider (auth, cache update, websocket connect)."""
        ...

    async def shutdown(self) -> None:
        """Clean shutdown (disconnect websocket, flush cache)."""
        ...

    async def get_options_chain(
        self, underlying: Underlying, expiry: date
    ) -> tuple[OptionsChain, dict[str, GreeksSnapshot]]:
        """Get options chain with Greeks for an underlying at a specific expiry."""
        ...

    async def get_market_snapshot(self, underlying: Underlying) -> MarketSnapshot:
        """Get current market state for an underlying."""
        ...

    async def get_funds(self) -> Decimal:
        """Get available trading capital."""
        ...

    async def get_positions(self) -> list[dict]:
        """Get current open positions."""
        ...

    async def get_candles(
        self, symbol: str, resolution: str, periods: int
    ) -> pd.DataFrame:
        """Get historical OHLCV candles from local cache."""
        ...
