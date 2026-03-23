"""Tests for DailyReportEngine pipeline."""
import datetime as dt
from unittest.mock import MagicMock

import pytest

from quant.models.daily_report import ErrorCategory, ReportStatus, ReportType


@pytest.fixture
def mock_holiday_checker():
    checker = MagicMock()
    checker.is_trading_day.return_value = True
    checker.get_holiday_name.return_value = None
    checker.get_next_trading_day.return_value = dt.date(2026, 3, 24)
    return checker


@pytest.fixture
def mock_holiday_checker_holiday():
    checker = MagicMock()
    checker.is_trading_day.return_value = False
    checker.get_holiday_name.return_value = "Holi"
    checker.get_next_trading_day.return_value = dt.date(2026, 3, 27)
    return checker


class TestReportEngineHoliday:
    @pytest.mark.asyncio
    async def test_holiday_returns_holiday_report(self, mock_holiday_checker_holiday):
        from quant.report.engine import DailyReportEngine
        engine = DailyReportEngine(holiday_checker=mock_holiday_checker_holiday)
        report = await engine.generate(ReportType.MORNING, dry_run=True)
        assert report.report_status == ReportStatus.MARKET_HOLIDAY
        assert report.holiday_name == "Holi"
        assert report.next_trading_day == dt.date(2026, 3, 27)
        assert report.market_macros is None


class TestReportEngineError:
    @pytest.mark.asyncio
    async def test_market_data_failure_returns_error(self, mock_holiday_checker):
        from quant.report.engine import DailyReportEngine
        engine = DailyReportEngine(holiday_checker=mock_holiday_checker)
        report = await engine.generate(ReportType.EVENING, dry_run=True)
        assert report.report_status == ReportStatus.ERROR
        assert report.error_category == ErrorCategory.MARKET_DATA_UNAVAILABLE
