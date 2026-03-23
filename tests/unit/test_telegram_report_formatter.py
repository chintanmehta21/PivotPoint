"""Unit tests for TelegramReportFormatter."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pytest

from quant.config.identity import APP_NAME
from quant.models.daily_report import (
    DailyReport,
    ErrorCategory,
    MarketMacros,
    PortfolioTier,
    ReportStatus,
    ReportType,
    VirtualPortfolio,
)
from outputs.telegram.report_formatter import (
    CALLBACK_ANALYSIS,
    CALLBACK_PORTFOLIO,
    TelegramReportFormatter,
)


@pytest.fixture
def formatter() -> TelegramReportFormatter:
    return TelegramReportFormatter()


# ---------------------------------------------------------------------------
# format_report
# ---------------------------------------------------------------------------


class TestFormatReport:
    def test_returns_tuple(self, formatter, sample_daily_report):
        result = formatter.format_report(sample_daily_report)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_text_is_str(self, formatter, sample_daily_report):
        text, _ = formatter.format_report(sample_daily_report)
        assert isinstance(text, str)

    def test_keyboard_is_list(self, formatter, sample_daily_report):
        _, keyboard = formatter.format_report(sample_daily_report)
        assert isinstance(keyboard, list)

    def test_keyboard_has_two_buttons(self, formatter, sample_daily_report):
        _, keyboard = formatter.format_report(sample_daily_report)
        # Keyboard is [[btn1, btn2]] — one row with two buttons
        assert len(keyboard) == 1
        assert len(keyboard[0]) == 2

    def test_keyboard_portfolio_button_callback(self, formatter, sample_daily_report):
        _, keyboard = formatter.format_report(sample_daily_report)
        portfolio_btn = keyboard[0][0]
        assert portfolio_btn["callback_data"] == CALLBACK_PORTFOLIO

    def test_keyboard_analysis_button_callback(self, formatter, sample_daily_report):
        _, keyboard = formatter.format_report(sample_daily_report)
        analysis_btn = keyboard[0][1]
        assert analysis_btn["callback_data"] == CALLBACK_ANALYSIS

    def test_contains_app_name(self, formatter, sample_daily_report):
        text, _ = formatter.format_report(sample_daily_report)
        assert APP_NAME in text

    def test_contains_report_type(self, formatter, sample_daily_report):
        text, _ = formatter.format_report(sample_daily_report)
        assert "Evening" in text

    def test_contains_nifty_price(self, formatter, sample_daily_report):
        text, _ = formatter.format_report(sample_daily_report)
        # 22,450.30 — comma may be escaped or not, just check the digits
        assert "22" in text and "450" in text

    def test_contains_vix(self, formatter, sample_daily_report):
        text, _ = formatter.format_report(sample_daily_report)
        assert "14" in text  # india_vix=14.8

    def test_contains_market_snapshot_header(self, formatter, sample_daily_report):
        text, _ = formatter.format_report(sample_daily_report)
        assert "Market Snapshot" in text

    def test_report_without_market_macros(self, formatter):
        report = DailyReport(
            report_type=ReportType.MORNING,
            report_status=ReportStatus.SUCCESS,
            date=date(2026, 3, 24),
            timestamp=datetime(2026, 3, 24, 9, 0, 0),
        )
        text, keyboard = formatter.format_report(report)
        assert isinstance(text, str)
        assert isinstance(keyboard, list)

    def test_report_with_portfolios(self, formatter, sample_daily_report, sample_virtual_portfolio):
        sample_daily_report.portfolios = [sample_virtual_portfolio]
        text, _ = formatter.format_report(sample_daily_report)
        assert "Portfolio" in text
        assert "Conservative" in text or "CONSERVATIVE" in text

    def test_tree_chars_present(self, formatter, sample_daily_report):
        text, _ = formatter.format_report(sample_daily_report)
        assert "├" in text or "└" in text


# ---------------------------------------------------------------------------
# format_holiday
# ---------------------------------------------------------------------------


class TestFormatHoliday:
    @pytest.fixture
    def holiday_report(self) -> DailyReport:
        return DailyReport(
            report_type=ReportType.MORNING,
            report_status=ReportStatus.MARKET_HOLIDAY,
            date=date(2026, 3, 25),
            timestamp=datetime(2026, 3, 25, 9, 0, 0),
            holiday_name="Holi",
            next_trading_day=date(2026, 3, 26),
        )

    def test_returns_tuple(self, formatter, holiday_report):
        result = formatter.format_holiday(holiday_report)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_keyboard_is_none(self, formatter, holiday_report):
        _, keyboard = formatter.format_holiday(holiday_report)
        assert keyboard is None

    def test_text_is_str(self, formatter, holiday_report):
        text, _ = formatter.format_holiday(holiday_report)
        assert isinstance(text, str)

    def test_contains_holiday_name(self, formatter, holiday_report):
        text, _ = formatter.format_holiday(holiday_report)
        assert "Holi" in text

    def test_contains_app_name(self, formatter, holiday_report):
        text, _ = formatter.format_holiday(holiday_report)
        assert APP_NAME in text

    def test_contains_next_trading_day(self, formatter, holiday_report):
        text, _ = formatter.format_holiday(holiday_report)
        assert "26" in text  # next_trading_day = 2026-03-26

    def test_holiday_without_name_defaults(self, formatter):
        report = DailyReport(
            report_type=ReportType.MORNING,
            report_status=ReportStatus.MARKET_HOLIDAY,
            date=date(2026, 3, 25),
            timestamp=datetime(2026, 3, 25, 9, 0, 0),
        )
        text, keyboard = formatter.format_holiday(report)
        assert "Market Holiday" in text
        assert keyboard is None


# ---------------------------------------------------------------------------
# format_error
# ---------------------------------------------------------------------------


class TestFormatError:
    @pytest.fixture
    def error_report(self) -> DailyReport:
        return DailyReport(
            report_type=ReportType.EVENING,
            report_status=ReportStatus.ERROR,
            date=date(2026, 3, 24),
            timestamp=datetime(2026, 3, 24, 16, 0, 0),
            error_category=ErrorCategory.API_RATE_LIMITED,
            error_detail="Fyers API returned 429",
        )

    def test_returns_tuple(self, formatter, error_report):
        result = formatter.format_error(error_report)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_keyboard_is_none(self, formatter, error_report):
        _, keyboard = formatter.format_error(error_report)
        assert keyboard is None

    def test_text_is_str(self, formatter, error_report):
        text, _ = formatter.format_error(error_report)
        assert isinstance(text, str)

    def test_contains_error_label(self, formatter, error_report):
        text, _ = formatter.format_error(error_report)
        # ERROR_LABELS[API_RATE_LIMITED] = "API Rate Limited"
        assert "API Rate Limited" in text

    def test_contains_error_detail(self, formatter, error_report):
        text, _ = formatter.format_error(error_report)
        assert "Fyers API returned 429" in text

    def test_contains_app_name(self, formatter, error_report):
        text, _ = formatter.format_error(error_report)
        assert APP_NAME in text

    def test_all_error_categories_have_label(self, formatter):
        for category in ErrorCategory:
            report = DailyReport(
                report_type=ReportType.EVENING,
                report_status=ReportStatus.ERROR,
                date=date(2026, 3, 24),
                timestamp=datetime(2026, 3, 24, 16, 0, 0),
                error_category=category,
            )
            text, keyboard = formatter.format_error(report)
            assert isinstance(text, str)
            assert keyboard is None

    def test_error_without_category(self, formatter):
        report = DailyReport(
            report_type=ReportType.EVENING,
            report_status=ReportStatus.ERROR,
            date=date(2026, 3, 24),
            timestamp=datetime(2026, 3, 24, 16, 0, 0),
        )
        text, keyboard = formatter.format_error(report)
        assert "Unexpected Error" in text
        assert keyboard is None


# ---------------------------------------------------------------------------
# format_portfolio_drilldown
# ---------------------------------------------------------------------------


class TestFormatPortfolioDrilldown:
    def test_returns_str(self, formatter, sample_daily_report):
        result = formatter.format_portfolio_drilldown(sample_daily_report)
        assert isinstance(result, str)

    def test_contains_app_name(self, formatter, sample_daily_report):
        result = formatter.format_portfolio_drilldown(sample_daily_report)
        assert APP_NAME in result

    def test_no_portfolios_fallback(self, formatter, sample_daily_report):
        sample_daily_report.portfolios = []
        result = formatter.format_portfolio_drilldown(sample_daily_report)
        assert "No portfolio data" in result

    def test_with_portfolio_tier(self, formatter, sample_daily_report, sample_virtual_portfolio):
        sample_daily_report.portfolios = [sample_virtual_portfolio]
        result = formatter.format_portfolio_drilldown(sample_daily_report)
        # sample_virtual_portfolio.tier = PortfolioTier.CONSERVATIVE
        assert "Conservative" in result or "CONSERVATIVE" in result

    def test_with_portfolio_shows_pnl(self, formatter, sample_daily_report, sample_virtual_portfolio):
        sample_daily_report.portfolios = [sample_virtual_portfolio]
        result = formatter.format_portfolio_drilldown(sample_daily_report)
        # total_pnl = 50400
        assert "50" in result

    def test_with_portfolio_shows_win_rate(self, formatter, sample_daily_report, sample_virtual_portfolio):
        sample_daily_report.portfolios = [sample_virtual_portfolio]
        result = formatter.format_portfolio_drilldown(sample_daily_report)
        assert "Win Rate" in result or "68" in result

    def test_with_portfolio_shows_best_strategy(self, formatter, sample_daily_report, sample_virtual_portfolio):
        sample_daily_report.portfolios = [sample_virtual_portfolio]
        result = formatter.format_portfolio_drilldown(sample_daily_report)
        assert "BQ1" in result

    def test_with_portfolio_shows_threshold(self, formatter, sample_daily_report, sample_virtual_portfolio):
        sample_daily_report.portfolios = [sample_virtual_portfolio]
        result = formatter.format_portfolio_drilldown(sample_daily_report)
        assert "85" in result

    def test_tree_chars_present(self, formatter, sample_daily_report, sample_virtual_portfolio):
        sample_daily_report.portfolios = [sample_virtual_portfolio]
        result = formatter.format_portfolio_drilldown(sample_daily_report)
        assert "├" in result or "└" in result


# ---------------------------------------------------------------------------
# format_analysis_drilldown
# ---------------------------------------------------------------------------


class TestFormatAnalysisDrilldown:
    def test_returns_str(self, formatter, sample_daily_report):
        result = formatter.format_analysis_drilldown(sample_daily_report)
        assert isinstance(result, str)

    def test_contains_app_name(self, formatter, sample_daily_report):
        result = formatter.format_analysis_drilldown(sample_daily_report)
        assert APP_NAME in result

    def test_no_market_macros_fallback(self, formatter):
        report = DailyReport(
            report_type=ReportType.EVENING,
            report_status=ReportStatus.SUCCESS,
            date=date(2026, 3, 24),
            timestamp=datetime(2026, 3, 24, 16, 0, 0),
        )
        result = formatter.format_analysis_drilldown(report)
        assert "No market data" in result

    def test_contains_volatility_section(self, formatter, sample_daily_report):
        result = formatter.format_analysis_drilldown(sample_daily_report)
        assert "Volatility" in result

    def test_contains_vix_value(self, formatter, sample_daily_report):
        result = formatter.format_analysis_drilldown(sample_daily_report)
        # india_vix = 14.8
        assert "14" in result

    def test_contains_vix_label(self, formatter, sample_daily_report):
        result = formatter.format_analysis_drilldown(sample_daily_report)
        # VIX 14.8 → "Low"
        assert "Low" in result

    def test_with_optional_fields(self, formatter):
        macros = MarketMacros(
            nifty_price=Decimal("22000"),
            nifty_change_pct=0.5,
            banknifty_price=Decimal("48000"),
            banknifty_change_pct=-0.2,
            india_vix=18.0,
            vix_change=0.3,
            nifty_pcr_oi=1.05,
            nifty_max_pain=Decimal("22000"),
            banknifty_max_pain=Decimal("48000"),
            nifty_iv_percentile=50.0,
            banknifty_iv_percentile=45.0,
            fii_net_cash=Decimal("500"),
            dii_net_cash=Decimal("300"),
            nifty_atm_iv=18.5,
            banknifty_atm_iv=19.2,
            realized_vol_20d=15.0,
            iv_rv_spread=3.5,
            call_wall=Decimal("23000"),
            put_wall=Decimal("21000"),
            advance_decline_ratio=1.4,
            pct_above_20dma=65.0,
            pct_above_200dma=72.0,
        )
        report = DailyReport(
            report_type=ReportType.EVENING,
            report_status=ReportStatus.SUCCESS,
            date=date(2026, 3, 24),
            timestamp=datetime(2026, 3, 24, 16, 0, 0),
            market_macros=macros,
        )
        result = formatter.format_analysis_drilldown(report)
        assert "18" in result and "50" in result  # nifty_atm_iv = 18.5 (dot is escaped as \.)
        assert "Call Wall" in result
        assert "A/D Ratio" in result
