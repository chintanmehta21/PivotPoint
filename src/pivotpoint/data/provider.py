"""Market data provider interface (Protocol)."""
from __future__ import annotations
from datetime import date
from typing import Protocol
from pivotpoint.utils.types import Underlying
from pivotpoint.models.market import MarketSnapshot, OptionsChain

class MarketDataProvider(Protocol):
    """Protocol for market data providers. Primary implementation: Fyers API."""

    async def get_options_chain(self, underlying: Underlying, expiry: date) -> OptionsChain:
        """Get the options chain for an underlying at a specific expiry."""
        ...

    async def get_market_snapshot(self, underlying: Underlying) -> MarketSnapshot:
        """Get current market state for an underlying."""
        ...
