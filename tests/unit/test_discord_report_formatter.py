"""Tests for DiscordReportFormatter."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import discord
import pytest

from quant.config.identity import APP_NAME
from quant.models.daily_report import (
    DailyReport,
    ErrorCategory,
    MarketMacros,
    PortfolioTier,
    ReportStatus,
    ReportType,
    StrategyResult,
    VirtualPortfolio,
)
from quant.utils.types import Direction, TimeFrame
from outputs.discord.report_formatter import DiscordReportFormatter


@pytest.fixture
def formatter() -> DiscordReportFormatter:
    return DiscordReportFormatter()


# ---------------------------------------------------------------------------
# format_report
# ---------------------------------------------------------------------------


def test_format_report_returns_embed(formatter, sample_daily_report):
    result = formatter.format_report(sample_daily_report)
    assert isinstance(result, discord.Embed)


def test_format_report_color_is_gold(formatter, sample_daily_report):
    result = formatter.format_report(sample_daily_report)
    assert result.color == discord.Color.gold()


def test_format_report_title_contains_app_name(formatter, sample_daily_report):
    result = formatter.format_report(sample_daily_report)
    assert APP_NAME in result.title


def test_format_report_title_contains_date(formatter, sample_daily_report):
    result = formatter.format_report(sample_daily_report)
    assert str(sample_daily_report.date) in result.title


def test_format_report_market_macros_nifty_field(formatter, sample_daily_report):
    result = formatter.format_report(sample_daily_report)
    field_names = [f.name for f in result.fields]
    assert "NIFTY" in field_names


def test_format_report_market_macros_vix_field(formatter, sample_daily_report):
    result = formatter.format_report(sample_daily_report)
    field_names = [f.name for f in result.fields]
    assert "India VIX" in field_names


def test_format_report_top_bullish_included(formatter, sample_daily_report, sample_signal):
    from quant.models.daily_report import StrategyResult

    sample_daily_report.top_3_bullish = [
        StrategyResult(
            strategy_id="BW1",
            strategy_name="Bullish Weekly Iron Condor",
            direction=Direction.BULLISH,
            timeframe=TimeFrame.WEEKLY,
            confidence_score=82.0,
        )
    ]
    result = formatter.format_report(sample_daily_report)
    field_names = [f.name for f in result.fields]
    assert "Top Bullish Setups" in field_names


def test_format_report_top_bearish_included(formatter, sample_daily_report):
    sample_daily_report.top_3_bearish = [
        StrategyResult(
            strategy_id="BrM2",
            strategy_name="Bearish Monthly Bear Put",
            direction=Direction.BEARISH,
            timeframe=TimeFrame.MONTHLY,
            confidence_score=77.0,
        )
    ]
    result = formatter.format_report(sample_daily_report)
    field_names = [f.name for f in result.fields]
    assert "Top Bearish Setups" in field_names


def test_format_report_footer_contains_app_name(formatter, sample_daily_report):
    result = formatter.format_report(sample_daily_report)
    assert APP_NAME in result.footer.text


def test_format_report_no_macros_still_returns_embed(formatter):
    report = DailyReport(
        report_type=ReportType.MORNING,
        report_status=ReportStatus.SUCCESS,
        date=date(2026, 3, 24),
        timestamp=datetime(2026, 3, 24, 9, 0, 0),
    )
    result = formatter.format_report(report)
    assert isinstance(result, discord.Embed)


# ---------------------------------------------------------------------------
# format_holiday
# ---------------------------------------------------------------------------


def test_format_holiday_returns_embed(formatter):
    report = DailyReport(
        report_type=ReportType.MORNING,
        report_status=ReportStatus.MARKET_HOLIDAY,
        date=date(2026, 3, 25),
        timestamp=datetime(2026, 3, 25, 9, 0, 0),
        holiday_name="Holi",
        next_trading_day=date(2026, 3, 26),
    )
    result = formatter.format_holiday(report)
    assert isinstance(result, discord.Embed)


def test_format_holiday_color_is_green(formatter):
    report = DailyReport(
        report_type=ReportType.MORNING,
        report_status=ReportStatus.MARKET_HOLIDAY,
        date=date(2026, 3, 25),
        timestamp=datetime(2026, 3, 25, 9, 0, 0),
        holiday_name="Holi",
    )
    result = formatter.format_holiday(report)
    assert result.color == discord.Color.green()


def test_format_holiday_title_contains_app_name(formatter):
    report = DailyReport(
        report_type=ReportType.MORNING,
        report_status=ReportStatus.MARKET_HOLIDAY,
        date=date(2026, 3, 25),
        timestamp=datetime(2026, 3, 25, 9, 0, 0),
        holiday_name="Holi",
    )
    result = formatter.format_holiday(report)
    assert APP_NAME in result.title


def test_format_holiday_description_contains_holiday_name(formatter):
    report = DailyReport(
        report_type=ReportType.MORNING,
        report_status=ReportStatus.MARKET_HOLIDAY,
        date=date(2026, 3, 25),
        timestamp=datetime(2026, 3, 25, 9, 0, 0),
        holiday_name="Holi",
    )
    result = formatter.format_holiday(report)
    assert "Holi" in result.description


def test_format_holiday_next_trading_day_field(formatter):
    report = DailyReport(
        report_type=ReportType.MORNING,
        report_status=ReportStatus.MARKET_HOLIDAY,
        date=date(2026, 3, 25),
        timestamp=datetime(2026, 3, 25, 9, 0, 0),
        holiday_name="Holi",
        next_trading_day=date(2026, 3, 26),
    )
    result = formatter.format_holiday(report)
    field_names = [f.name for f in result.fields]
    assert "Next Trading Day" in field_names


def test_format_holiday_no_next_trading_day(formatter):
    report = DailyReport(
        report_type=ReportType.MORNING,
        report_status=ReportStatus.MARKET_HOLIDAY,
        date=date(2026, 3, 25),
        timestamp=datetime(2026, 3, 25, 9, 0, 0),
        holiday_name="Holi",
    )
    result = formatter.format_holiday(report)
    assert isinstance(result, discord.Embed)


# ---------------------------------------------------------------------------
# format_error
# ---------------------------------------------------------------------------


def test_format_error_returns_embed(formatter):
    report = DailyReport(
        report_type=ReportType.MORNING,
        report_status=ReportStatus.ERROR,
        date=date(2026, 3, 24),
        timestamp=datetime(2026, 3, 24, 9, 0, 0),
        error_category=ErrorCategory.API_RATE_LIMITED,
        error_detail="Too many requests within 1 minute.",
    )
    result = formatter.format_error(report)
    assert isinstance(result, discord.Embed)


def test_format_error_color_is_red(formatter):
    report = DailyReport(
        report_type=ReportType.MORNING,
        report_status=ReportStatus.ERROR,
        date=date(2026, 3, 24),
        timestamp=datetime(2026, 3, 24, 9, 0, 0),
        error_category=ErrorCategory.UNKNOWN_ERROR,
    )
    result = formatter.format_error(report)
    assert result.color == discord.Color.red()


def test_format_error_title_contains_app_name(formatter):
    report = DailyReport(
        report_type=ReportType.MORNING,
        report_status=ReportStatus.ERROR,
        date=date(2026, 3, 24),
        timestamp=datetime(2026, 3, 24, 9, 0, 0),
        error_category=ErrorCategory.AUTHENTICATION_EXPIRED,
    )
    result = formatter.format_error(report)
    assert APP_NAME in result.title


def test_format_error_description_contains_label(formatter):
    report = DailyReport(
        report_type=ReportType.MORNING,
        report_status=ReportStatus.ERROR,
        date=date(2026, 3, 24),
        timestamp=datetime(2026, 3, 24, 9, 0, 0),
        error_category=ErrorCategory.API_RATE_LIMITED,
    )
    result = formatter.format_error(report)
    assert "API Rate Limited" in result.description


def test_format_error_detail_field_when_present(formatter):
    report = DailyReport(
        report_type=ReportType.MORNING,
        report_status=ReportStatus.ERROR,
        date=date(2026, 3, 24),
        timestamp=datetime(2026, 3, 24, 9, 0, 0),
        error_category=ErrorCategory.DISPATCH_FAILED,
        error_detail="Channel not found.",
    )
    result = formatter.format_error(report)
    field_names = [f.name for f in result.fields]
    assert "Detail" in field_names


def test_format_error_no_detail_no_extra_field(formatter):
    report = DailyReport(
        report_type=ReportType.MORNING,
        report_status=ReportStatus.ERROR,
        date=date(2026, 3, 24),
        timestamp=datetime(2026, 3, 24, 9, 0, 0),
        error_category=ErrorCategory.UNKNOWN_ERROR,
    )
    result = formatter.format_error(report)
    field_names = [f.name for f in result.fields]
    assert "Detail" not in field_names


def test_format_error_no_category_fallback(formatter):
    report = DailyReport(
        report_type=ReportType.MORNING,
        report_status=ReportStatus.ERROR,
        date=date(2026, 3, 24),
        timestamp=datetime(2026, 3, 24, 9, 0, 0),
    )
    result = formatter.format_error(report)
    assert "Unexpected Error" in result.description


# ---------------------------------------------------------------------------
# format_portfolio_drilldown
# ---------------------------------------------------------------------------


def test_format_portfolio_drilldown_returns_embed(formatter, sample_daily_report, sample_virtual_portfolio):
    sample_daily_report.portfolios = [sample_virtual_portfolio]
    result = formatter.format_portfolio_drilldown(sample_daily_report)
    assert isinstance(result, discord.Embed)


def test_format_portfolio_drilldown_color_is_blurple(formatter, sample_daily_report, sample_virtual_portfolio):
    sample_daily_report.portfolios = [sample_virtual_portfolio]
    result = formatter.format_portfolio_drilldown(sample_daily_report)
    assert result.color == discord.Color.blurple()


def test_format_portfolio_drilldown_title_contains_app_name(formatter, sample_daily_report, sample_virtual_portfolio):
    sample_daily_report.portfolios = [sample_virtual_portfolio]
    result = formatter.format_portfolio_drilldown(sample_daily_report)
    assert APP_NAME in result.title


def test_format_portfolio_drilldown_tier_field_present(formatter, sample_daily_report, sample_virtual_portfolio):
    sample_daily_report.portfolios = [sample_virtual_portfolio]
    result = formatter.format_portfolio_drilldown(sample_daily_report)
    field_names = [f.name for f in result.fields]
    assert any("CONSERVATIVE" in name for name in field_names)


def test_format_portfolio_drilldown_three_tiers(formatter, sample_daily_report):
    sample_daily_report.portfolios = [
        VirtualPortfolio(
            tier=PortfolioTier.CONSERVATIVE,
            threshold=85,
            active_positions=2,
            total_trades=20,
            realized_pnl=Decimal("30000"),
            unrealized_pnl=Decimal("5000"),
            total_pnl=Decimal("35000"),
            win_rate=0.70,
            best_strategy="BW1",
            worst_strategy="BrM2",
        ),
        VirtualPortfolio(
            tier=PortfolioTier.MODERATE,
            threshold=75,
            active_positions=4,
            total_trades=35,
            realized_pnl=Decimal("55000"),
            unrealized_pnl=Decimal("12000"),
            total_pnl=Decimal("67000"),
            win_rate=0.63,
            best_strategy="BQ2",
            worst_strategy="BrW3",
        ),
        VirtualPortfolio(
            tier=PortfolioTier.AGGRESSIVE,
            threshold=0,
            active_positions=7,
            total_trades=50,
            realized_pnl=Decimal("90000"),
            unrealized_pnl=Decimal("20000"),
            total_pnl=Decimal("110000"),
            win_rate=0.58,
            best_strategy="BM3",
            worst_strategy="BrQ1",
        ),
    ]
    result = formatter.format_portfolio_drilldown(sample_daily_report)
    assert len(result.fields) == 3


def test_format_portfolio_drilldown_empty_portfolios(formatter, sample_daily_report):
    sample_daily_report.portfolios = []
    result = formatter.format_portfolio_drilldown(sample_daily_report)
    assert isinstance(result, discord.Embed)
    assert len(result.fields) == 0


# ---------------------------------------------------------------------------
# format_analysis_drilldown
# ---------------------------------------------------------------------------


def test_format_analysis_drilldown_returns_embed(formatter, sample_daily_report):
    result = formatter.format_analysis_drilldown(sample_daily_report)
    assert isinstance(result, discord.Embed)


def test_format_analysis_drilldown_color_is_blurple(formatter, sample_daily_report):
    result = formatter.format_analysis_drilldown(sample_daily_report)
    assert result.color == discord.Color.blurple()


def test_format_analysis_drilldown_title_contains_app_name(formatter, sample_daily_report):
    result = formatter.format_analysis_drilldown(sample_daily_report)
    assert APP_NAME in result.title


def test_format_analysis_drilldown_no_macros_still_returns_embed(formatter):
    report = DailyReport(
        report_type=ReportType.EVENING,
        report_status=ReportStatus.SUCCESS,
        date=date(2026, 3, 24),
        timestamp=datetime(2026, 3, 24, 16, 0, 0),
    )
    result = formatter.format_analysis_drilldown(report)
    assert isinstance(result, discord.Embed)


def test_format_analysis_drilldown_dealer_positioning_field(formatter, sample_daily_report):
    sample_daily_report.market_macros.net_gamma_exposure = Decimal("12500000")
    sample_daily_report.market_macros.call_wall = Decimal("23000")
    sample_daily_report.market_macros.put_wall = Decimal("22000")
    result = formatter.format_analysis_drilldown(sample_daily_report)
    field_names = [f.name for f in result.fields]
    assert "Dealer Positioning" in field_names


def test_format_analysis_drilldown_support_resistance_fields(formatter, sample_daily_report):
    sample_daily_report.market_macros.nifty_support_levels = [Decimal("22000"), Decimal("21800")]
    sample_daily_report.market_macros.nifty_resistance_levels = [Decimal("22800"), Decimal("23000")]
    result = formatter.format_analysis_drilldown(sample_daily_report)
    field_names = [f.name for f in result.fields]
    assert "NIFTY Support" in field_names
    assert "NIFTY Resistance" in field_names


def test_format_analysis_drilldown_technical_signals_field(formatter, sample_daily_report):
    sample_daily_report.market_macros.supertrend_signal = "BULLISH"
    sample_daily_report.market_macros.nifty_rsi = 58.3
    sample_daily_report.market_macros.nifty_macd_state = "POSITIVE_CROSSOVER"
    result = formatter.format_analysis_drilldown(sample_daily_report)
    field_names = [f.name for f in result.fields]
    assert "Technical Signals" in field_names


def test_format_analysis_drilldown_footer_contains_app_name(formatter, sample_daily_report):
    result = formatter.format_analysis_drilldown(sample_daily_report)
    assert APP_NAME in result.footer.text
