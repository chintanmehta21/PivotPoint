"""Fetches market macro data from Fyers API and NSE.

NOTE: This is a stub implementation. Real Fyers API integration
will be implemented when MarketDataProvider is connected (Phase 4).
Currently returns placeholder data for pipeline testing.
"""

from __future__ import annotations

import structlog

from quant.config.identity import APP_NAME
from quant.models.daily_report import MarketMacros, ReportType

logger = structlog.get_logger()


class MarketDataCollector:
    """Collects all market macro metrics for the daily report."""

    async def collect(self, report_type: ReportType) -> MarketMacros:
        """Fetch market data. Raises on failure."""
        logger.info("Collecting market data", report_type=report_type.value, app=APP_NAME)
        raise NotImplementedError(
            "MarketDataCollector requires Fyers API integration. Use --dry-run with mock data for testing."
        )
