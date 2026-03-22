"""Base formatter for output channels."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from quant.models.signals import SignalPayload


class BaseFormatter(ABC):
    """Abstract base for signal formatters."""

    @abstractmethod
    def format_entry(self, signal: SignalPayload) -> Any:
        """Format an entry signal."""
        ...

    @abstractmethod
    def format_exit(self, signal: SignalPayload) -> Any:
        """Format an exit signal."""
        ...

    @abstractmethod
    def format_adjustment(self, signal: SignalPayload) -> Any:
        """Format an adjustment signal."""
        ...
