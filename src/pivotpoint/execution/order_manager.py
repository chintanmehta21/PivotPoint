"""Broker-agnostic order management interface.

FUTURE: Implement concrete providers (Fyers, Zerodha, etc.)
"""
from __future__ import annotations
from typing import Protocol
from pydantic import BaseModel

from pivotpoint.models.contracts import MultiLegPosition


class OrderResult(BaseModel):
    """Result of an order placement."""
    order_id: str
    status: str  # PLACED, FILLED, REJECTED, CANCELLED
    message: str = ""


class OrderManager(Protocol):
    """Protocol for order management — broker integration point.

    # FUTURE: Fyers API integration for live order execution.
    """

    async def place_order(self, position: MultiLegPosition) -> OrderResult:
        """Place a multi-leg order."""
        ...

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an existing order."""
        ...

    async def get_status(self, order_id: str) -> OrderResult:
        """Get current order status."""
        ...
