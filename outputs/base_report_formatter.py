"""Base class for daily report formatters.

Separate from BaseFormatter (which handles individual signal alerts).
Report formatting has different methods: report, holiday, error, drill-downs.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

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
