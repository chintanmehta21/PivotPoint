"""Tests for layered holiday detection."""
import datetime as dt
from unittest.mock import patch

from quant.calendar.holiday_checker import HolidayChecker


class TestWeekendDetection:
    def test_saturday_is_not_trading_day(self):
        checker = HolidayChecker()
        assert checker.is_trading_day(dt.date(2026, 3, 28)) is False

    def test_sunday_is_not_trading_day(self):
        checker = HolidayChecker()
        assert checker.is_trading_day(dt.date(2026, 3, 29)) is False


class TestExchangeCalendars:
    @patch("quant.calendar.holiday_checker.HolidayChecker._check_nse_api", return_value=None)
    def test_known_weekday_is_trading(self, mock_nse):
        checker = HolidayChecker()
        assert checker.is_trading_day(dt.date(2026, 3, 23)) is True

    @patch("quant.calendar.holiday_checker.HolidayChecker._check_nse_api", return_value=None)
    def test_republic_day_is_holiday(self, mock_nse):
        checker = HolidayChecker()
        assert checker.is_trading_day(dt.date(2026, 1, 26)) is False


class TestNseApiLayer:
    def test_nse_says_holiday_overrides_xbom(self):
        checker = HolidayChecker()
        with patch.object(checker, "_check_nse_api", return_value=True):
            assert checker.is_trading_day(dt.date(2026, 3, 23)) is False

    def test_nse_api_failure_falls_back_to_xbom(self):
        checker = HolidayChecker()
        with patch.object(checker, "_check_nse_api", return_value=None):
            assert checker.is_trading_day(dt.date(2026, 3, 23)) is True


class TestYamlOverrides:
    def test_yaml_holiday_override(self):
        checker = HolidayChecker()
        checker._overrides = [{"date": "2026-03-23", "status": "HOLIDAY", "name": "Test Holiday"}]
        assert checker.is_trading_day(dt.date(2026, 3, 23)) is False

    def test_yaml_open_override(self):
        checker = HolidayChecker()
        checker._overrides = [{"date": "2026-01-26", "status": "OPEN"}]
        assert checker.is_trading_day(dt.date(2026, 1, 26)) is True

    def test_yaml_override_name(self):
        checker = HolidayChecker()
        checker._overrides = [{"date": "2026-03-26", "status": "HOLIDAY", "name": "Holi"}]
        assert checker.get_holiday_name(dt.date(2026, 3, 26)) == "Holi"


class TestNextPreviousTradingDay:
    def test_next_trading_day_skips_weekend(self):
        checker = HolidayChecker()
        with patch.object(checker, "_check_nse_api", return_value=None):
            next_day = checker.get_next_trading_day(dt.date(2026, 3, 27))
            assert next_day == dt.date(2026, 3, 30)

    def test_previous_trading_day_skips_weekend(self):
        checker = HolidayChecker()
        with patch.object(checker, "_check_nse_api", return_value=None):
            prev_day = checker.get_previous_trading_day(dt.date(2026, 3, 30))
            assert prev_day == dt.date(2026, 3, 27)
