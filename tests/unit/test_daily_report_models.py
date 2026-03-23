"""Tests for daily report data models."""
from datetime import date, datetime
from decimal import Decimal

from quant.models.daily_report import (
    ERROR_LABELS,
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


class TestEnums:
    def test_report_type_values(self):
        assert ReportType.MORNING == "MORNING"
        assert ReportType.EVENING == "EVENING"

    def test_report_status_values(self):
        assert ReportStatus.SUCCESS == "SUCCESS"
        assert ReportStatus.MARKET_HOLIDAY == "MARKET_HOLIDAY"
        assert ReportStatus.ERROR == "ERROR"

    def test_error_category_values(self):
        assert len(ErrorCategory) == 7
        assert ErrorCategory.UNKNOWN_ERROR == "UNKNOWN_ERROR"

    def test_portfolio_tier_values(self):
        assert PortfolioTier.CONSERVATIVE == "CONSERVATIVE"
        assert PortfolioTier.MODERATE == "MODERATE"
        assert PortfolioTier.AGGRESSIVE == "AGGRESSIVE"

    def test_error_labels_all_categories_have_labels(self):
        for cat in ErrorCategory:
            assert cat in ERROR_LABELS, f"Missing label for {cat}"
            assert isinstance(ERROR_LABELS[cat], str)


class TestMarketMacros:
    def test_required_fields_only(self):
        macros = MarketMacros(
            nifty_price=Decimal("22450.30"),
            nifty_change_pct=1.2,
            banknifty_price=Decimal("48120.50"),
            banknifty_change_pct=-0.4,
            india_vix=14.8,
            vix_change=-0.6,
            nifty_pcr_oi=1.12,
            nifty_max_pain=Decimal("22500"),
            banknifty_max_pain=Decimal("48000"),
            nifty_iv_percentile=42.0,
            banknifty_iv_percentile=38.0,
            fii_net_cash=Decimal("-1240"),
            dii_net_cash=Decimal("890"),
        )
        assert macros.nifty_price == Decimal("22450.30")
        assert macros.advance_decline_ratio is None
        assert macros.net_gamma_exposure is None
        assert macros.nifty_support_levels == []

    def test_optional_ml_fields(self):
        macros = MarketMacros(
            nifty_price=Decimal("22450"),
            nifty_change_pct=1.2,
            banknifty_price=Decimal("48120"),
            banknifty_change_pct=-0.4,
            india_vix=14.8,
            vix_change=-0.6,
            nifty_pcr_oi=1.12,
            nifty_max_pain=Decimal("22500"),
            banknifty_max_pain=Decimal("48000"),
            nifty_iv_percentile=42.0,
            banknifty_iv_percentile=38.0,
            fii_net_cash=Decimal("-1240"),
            dii_net_cash=Decimal("890"),
            realized_vol_5d=0.15,
            pcr_momentum=0.02,
        )
        assert macros.realized_vol_5d == 0.15
        assert macros.pcr_momentum == 0.02


class TestStrategyResult:
    def test_no_signal(self):
        result = StrategyResult(
            strategy_id="BW1",
            strategy_name="Call Ratio Backspread",
            direction=Direction.BULLISH,
            timeframe=TimeFrame.WEEKLY,
            signal=None,
            confidence_score=None,
            error=None,
        )
        assert result.signal is None

    def test_with_error(self):
        result = StrategyResult(
            strategy_id="BW1",
            strategy_name="Call Ratio Backspread",
            direction=Direction.BULLISH,
            timeframe=TimeFrame.WEEKLY,
            signal=None,
            confidence_score=None,
            error="Insufficient market data",
        )
        assert result.error == "Insufficient market data"


class TestVirtualPortfolio:
    def test_creation(self):
        portfolio = VirtualPortfolio(
            tier=PortfolioTier.CONSERVATIVE,
            threshold=85,
            active_positions=3,
            total_trades=28,
            realized_pnl=Decimal("42300"),
            unrealized_pnl=Decimal("8100"),
            total_pnl=Decimal("50400"),
            win_rate=0.68,
            best_strategy="BQ1",
            worst_strategy="BrM2",
        )
        assert portfolio.tier == PortfolioTier.CONSERVATIVE
        assert portfolio.threshold == 85


class TestDailyReport:
    def test_success_report(self, sample_market_macros):
        report = DailyReport(
            report_type=ReportType.EVENING,
            report_status=ReportStatus.SUCCESS,
            date=date(2026, 3, 24),
            timestamp=datetime(2026, 3, 24, 16, 0, 0),
            holiday_name=None,
            next_trading_day=None,
            market_macros=sample_market_macros,
        )
        assert report.report_status == ReportStatus.SUCCESS
        assert report.strategy_results == []
        assert report.portfolios == []

    def test_holiday_report(self):
        report = DailyReport(
            report_type=ReportType.MORNING,
            report_status=ReportStatus.MARKET_HOLIDAY,
            date=date(2026, 3, 26),
            timestamp=datetime(2026, 3, 26, 8, 30, 0),
            holiday_name="Holi",
            next_trading_day=date(2026, 3, 27),
            market_macros=None,
        )
        assert report.holiday_name == "Holi"
        assert report.next_trading_day == date(2026, 3, 27)
        assert report.market_macros is None

    def test_error_report(self):
        report = DailyReport(
            report_type=ReportType.EVENING,
            report_status=ReportStatus.ERROR,
            date=date(2026, 3, 24),
            timestamp=datetime(2026, 3, 24, 16, 0, 0),
            holiday_name=None,
            next_trading_day=None,
            market_macros=None,
            error_category=ErrorCategory.MARKET_DATA_UNAVAILABLE,
            error_detail="Fyers API timeout after 30s",
        )
        assert report.error_category == ErrorCategory.MARKET_DATA_UNAVAILABLE
