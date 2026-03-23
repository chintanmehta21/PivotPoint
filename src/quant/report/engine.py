"""Daily report generation pipeline orchestrator."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

import structlog

from quant.calendar.holiday_checker import HolidayChecker
from quant.config.identity import APP_NAME
from quant.models.daily_report import (
    DailyReport,
    ErrorCategory,
    ReportStatus,
    ReportType,
)
from quant.report.market_data_collector import MarketDataCollector
from quant.report.portfolio_tracker import PortfolioTracker

logger = structlog.get_logger()
IST = ZoneInfo("Asia/Kolkata")

# Retry config — deferred until Fyers API is connected
_RETRY_CONFIG: dict[ErrorCategory, tuple[int, float]] = {
    ErrorCategory.MARKET_DATA_UNAVAILABLE: (3, 30.0),
    ErrorCategory.API_RATE_LIMITED: (3, 60.0),
    ErrorCategory.DISPATCH_FAILED: (2, 15.0),
}


class DailyReportEngine:
    def __init__(
        self,
        holiday_checker: HolidayChecker | None = None,
        market_data_collector: MarketDataCollector | None = None,
        portfolio_tracker: PortfolioTracker | None = None,
    ) -> None:
        self._holiday = holiday_checker or HolidayChecker()
        self._market = market_data_collector or MarketDataCollector()
        self._portfolio = portfolio_tracker or PortfolioTracker()

    async def generate(self, report_type: ReportType, dry_run: bool = False) -> DailyReport:
        today = date.today()
        now = datetime.now(tz=IST)
        logger.info("Generating daily report", report_type=report_type.value, date=str(today), app=APP_NAME)

        # Step 1: Holiday check
        if not self._holiday.is_trading_day(today):
            holiday_name = self._holiday.get_holiday_name(today) or "Market Holiday"
            next_day = self._holiday.get_next_trading_day(today)
            logger.info("Market holiday detected", holiday=holiday_name)
            return DailyReport(
                report_type=report_type,
                report_status=ReportStatus.MARKET_HOLIDAY,
                date=today,
                timestamp=now,
                holiday_name=holiday_name,
                next_trading_day=next_day,
            )

        # Step 2: Fetch market data
        try:
            macros = await self._market.collect(report_type)
        except NotImplementedError as e:
            logger.warning("Market data collector not implemented", error=str(e))
            return DailyReport(
                report_type=report_type,
                report_status=ReportStatus.ERROR,
                date=today,
                timestamp=now,
                error_category=ErrorCategory.MARKET_DATA_UNAVAILABLE,
                error_detail=str(e),
            )
        except Exception as e:
            logger.error("Market data collection failed", error=str(e))
            return DailyReport(
                report_type=report_type,
                report_status=ReportStatus.ERROR,
                date=today,
                timestamp=now,
                error_category=ErrorCategory.MARKET_DATA_UNAVAILABLE,
                error_detail=str(e),
            )

        # Steps 3-4: Strategy scan + portfolio snapshots
        portfolios = self._portfolio.get_snapshots()

        return DailyReport(
            report_type=report_type,
            report_status=ReportStatus.SUCCESS,
            date=today,
            timestamp=now,
            market_macros=macros,
            portfolios=portfolios,
        )
